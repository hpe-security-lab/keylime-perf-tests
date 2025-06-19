# Keylime Performance Testing Tools

This repo provides CLI tools for stress-testing a [Keylime](https://keylime.dev/) verifier install using the Keylime
Push Attestation Protocol. By simulating many simultaneous connections, these tools make it possible to obtain 
performance benchmarks within a given environment without having to deploy a whole fleet of attesters/agents.

To maximise throughput, two strategies are used for concurrency:

- Running the tests starts a number of worker process, by default one for each available processor thread.
- Each worker process issues requests using [asyncio](https://docs.python.org/3/library/asyncio.html), so that while the
  process is waiting for a response from the verifier, it can continue submitting attestations.

The typical operation of these tools is illustrated by the below diagram:

![The tools communicate with the Keylime verifier and PostgreSQL database to aggregate performance data](diagram.svg)


## Environment Setup

The performance testing tools in this repository assume a specific operating environment. You may set this up in the
manner shown in the above diagram, or you may co-locate the tools on the same system as your Keylime verifier install.
The latter approach limits how many attestations may be sent per unit of time, as both the client and server must 
utilise the same system resources.

The below instructions, split into parts A-C, cover both these setups. Other configurations are also possible
(see [Advanced Configurations](#advanced-configurations)).

> [!CAUTION]
> This guide is for configuring an environment for **testing only** and assumes you are deploying these components on a
> secure local network behind a firewall.
>
> **You should not use these instructions to set up a production environment.**


### A. Install and configure PostgreSQL

Keylime stores data in SQLite databases by default to ease first-time setup. As a simple file-backed datastore is easily
overwhelmed, a fully-featured traditional database engine is required instead.

The performance testing scripts assume a PostgreSQL install is available and will issue queries against it directly to 
bulk create mock agent and policy/reference measurement records for testing.

1. Install PostgreSQL using your system package manager. Assuming Ubuntu:

    ```
    sudo apt update
    sudo apt install postgresql
    ```

2. Set the password for the default "postgres" user account:

    ```
    $ sudo -u postgres psql
    postgres=# ALTER USER postgres with encrypted password 'postgres';
    postgres=# exit
    ```

    This sets the password to "postgres".

> [!TIP]
> If you get an error that your user account is not permitted to execute `psql` as user "postgres", try running
> the sudo command using sudo:
>
> ```
> sudo sudo -u postgres psql
> ``` 

3. Create a database for the Keylime verifier:

    ```console
    $ sudo -u postgres createdb verifierdb
    ```

4. Edit the configuration file for your PostgreSQL version:

    ```console
    $ psql --version
    psql (PostgreSQL) 16.9
    $ sudo nano /etc/postgresql/16/main/postgresql.conf
    ```

    You will want to set the following options:

    - `listen_addresses = '*'`: **(optional)** set if you intend to run the performance tests from another system
    - `port = 5432`
    - `shared_buffers`: it is suggested to set this to 25&ndash;40% of the memory of your system
    - `max_connections`: you may wish to increase this above the default of 100
    - `track_activity_query_size = 10000`: allows storage of executing queries in their entirety

> [!TIP]
> If you intend to run the tests from another system, you will need to ensure that any intermediary firewall is
> configured to allow connections to the system running PostgreSQL at port 5432.

5. **(Optional)** If you wish to run the performance tests from another system over the network, check that remote
    authentication is permitted:

    ```console
    $ sudo nano /etc/postgresql/16/main/pg_hba.conf
    ```

    Ensure the following lines are present:

    ```
    # TYPE  DATABASE        USER            ADDRESS                 METHOD
    host    all             all             0.0.0.0/0               scram-sha-256
    hostssl all             all             0.0.0.0/0               scram-sha-256
    ```

6. Restart the PostgreSQL service:

    ```console
    $ sudo systemctl restart postgresql.service
    ```


### B. Set up a verifier instance to test against

You will need a version of Keylime with push support enabled to receive attestations submitted by the test script.
Additionally, the script requires a small modification to the source. To set up an appropriate testing installation:

1. Obtain the pre-release version of Keylime with support for agent-driven attestation:

    ```
    git clone git@github.com:keylime/keylime.git
    cd keylime
    git fetch origin pull/1693/head:push-attestation
    git checkout push-attestation
    sudo ./installer.sh
    ```

2. Change the verifier to use a fixed challenge, instead of generating a new random value for each attestation. This is
    needed because the test scripts submit the same captured TPM quote for each attestation.

    Edit the `CertificationParameters.generate_challenge()` method (line ~388) in `keylime/models/verifier/evidence.py`:

    ```python
    def generate_challenge(self, bit_length):
        # self.challenge = Nonce.generate(bit_length)
        self.challenge = bytes.fromhex("49beed365aac777dae23564f5ad0ec")
    ```

> [!CAUTION]
> This change is to fascilitate the performance tests only and should not be used in production.

3. Update the verifier configuration file:

    ```
    sudo nano /etc/keylime/verifier.conf
    ```

    Set the following options:

    - `ip`: set to "0.0.0.0" if you intend to run the tests from another system or "127.0.0.1" otherwise
    - `port = 8881`
    - `database_url = "postgresql://postgres:postgres@127.0.0.1:5432/verifierdb"`
    - `quote_interval`: whatever value you desire, but it is suggested you set this to only a few seconds
    - `nonce_lifetime`: whatever value you desire, but 900 seconds (15 minutes) is suggested
    - `verification_timeout`: whatever value you desire, but 120 seconds (2 minutes) is suggested

> [!TIP]
> If you intend to run the tests from another system, you will need to ensure that any intermediary firewall is
> configured to allow connections to the system running the verifier at port 8881.

4. It is suggested you also change the logging settings to output additional information with each request:

    ```
    sudo nano /etc/keylime/logging.conf
    ```

    Make the following edits:

    ```
    # ...
    [formatter_formatter]
    format = %(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s %(reqidf)s
    # ...
    [logger_keylime]
    level = DEBUG
    # ...
    ```

5. Run the modified verifier:

    ```
    sudo python3 -m keylime.cmd.verifier
    ```


### C. Install the testing tools

1. On the system from which you wish to run the tests, download the repository and install the neccessary dependencies:

    ```
    git clone git@github.com:hpe-security-lab/keylime-perf-tests.git
    cd keylime-perf-tests
    pip install -r requirements.txt
    ```

2. Set the appropriate permissions on the two CLI tools:

    ```
    chmod 755 run_perf_tests
    chmod 755 report_results
    ```

3. You should now be able to run the scripts from the `keylime-perf-tests` directory. To see available options:

    ```
    ./run_perf_tests -h
    ```


## Usage

There are two CLI tools provided in this repo:

- `./run_perf_tests`: submits attestations and records results for each attempt
- `./report_results`: outputs summary reports for past test runs

These are explained individually below.

### Running the tests

The most basic usage of the `./run_perf_tests` tool is as follows, assuming you set up your testing environment in the
manner described above.

```
./run_perf_tests https://<verifier_ip>:8881 postgresql://postgres:postgres@<verifier_ip>:5432/verifierdb
```

Running this will:

- Start a number of worker processes equal to the the number of processor threads available on your system.
- Create an equivalent number of mock agent records each with identical policies and reference measurements.
- Begin performing attestations for each agent in sequence.

Because attestations are performed concurrently, they may not complete in the order they were initiated. The script will
continue submitting attestations until stopped by pressing Ctrl+C.

> [!IMPORTANT]  
> When the tests are stopped, the script will not exit immediately but will instead wait for any in-progress attestation
> tasks to finish. On completion, the mock agents and policies are deleted from the verifier and a summary of results
> are displayed.

#### Changing resource utilisation

You may wish to change the number of worker processes which are spawned or the number of mock agents which are created.
This can be done with the `-w` and `-a` options, respectively:

```
./run_perf_tests https://<verifier_ip>:8881 postgresql://postgres:postgres@<verifier_ip>:5432/verifierdb -w 5 -a 10
```

This will spawn 5 workers and perform attestations using 10 agents. If you don't provide `-a`, whatever value you 
specify for `-w` will be used.

#### Limit the number of attestations

Instead of performing attestation indefinitely, you may wish to only perform a set number per agent. This is achievable
with the `-t` option:

```
./run_perf_tests https://<verifier_ip>:8881 postgresql://postgres:postgres@<verifier_ip>:5432/verifierdb -a 2 -t 3
```

This will perform 3 attestation tasks for each of the 2 agents. So, 5 attestations total will be attempted.

> [!NOTE]  
> This does not directly limit how many requests are performed, as multiple requests may be performed per attestation
> and the number depends on the cofiguration and current state of the verifier. 

### Viewing past test runs

When the performance tests are run, each attestation task and its requests are output to a new file in the `./results`
directory. This file is named according to the timestamp at which tests were initiated.

To parse these results and obtain the summary report for a past test run, use the following command:

```
./report_results 20250606134858
```

This produces a report similar to the following:

```
─────────────────────────────────────────────────────────────────────────────────────────────────────────
                                           TEST RESULT SUMMARY
═════════════════════════════════════════════════════════════════════════════════════════════════════════

  Performed 17437 attestations in 1:14:22 (4462.4s)

  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                  Capabilities Negotiation Phase                                   │
  ├────────────────────────────────────────────────────┬──────────────────────────────────────────────┤
  │                Individual Requests                 │               Phase Executions               │
  ├────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │                         ok   retry    fail     all │                      success    fail     all │
  │                     ------  ------  ------  ------ │                     --------  ------  ------ │
  │ Create Requests:                                   │ Executions:                                  │
  │   Number             17437     905       0   18342 │   Number               17437       0   17437 │
  │   Percentage         95.1%    4.9%    0.0%         │   Percentage          100.0%    0.0%         │
  │ Durations:                                         │ Durations:                                   │
  │   Average             6.4s   952ms      --    6.1s │   Average               6.5s      --    6.5s │
  │   Shortest           314ms   746ms      --   314ms │   Shortest             314ms      --   314ms │
  │   Longest            17.8s    2.1s      --   17.8s │   Longest              17.8s      --   17.8s │
  └────────────────────────────────────────────────────┴──────────────────────────────────────────────┘
  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                      Evidence Handling Phase                                      │
  ├────────────────────────────────────────────────────┬──────────────────────────────────────────────┤
  │                Individual Requests                 │               Phase Executions               │
  ├────────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │                         ok   retry    fail     all │                      success    fail     all │
  │                     ------  ------  ------  ------ │                     --------  ------  ------ │
  │ Update Requests:                                   │ Executions:                                  │
  │   Number             17399       0      38   17437 │   Number               17399      38   17437 │
  │   Percentage         99.8%    0.0%    0.2%         │   Percentage           99.8%    0.2%         │
  │ Durations:                                         │ Durations:                                   │
  │   Average             2.3s      --    2.7s    2.3s │   Average               2.3s    2.7s    2.3s │
  │   Shortest            1.0s      --    1.1s    1.0s │   Shortest              1.0s    1.1s    1.0s │
  │   Longest            16.8s      --    5.4s   16.8s │   Longest              16.8s    5.4s   16.8s │
  └────────────────────────────────────────────────────┴──────────────────────────────────────────────┘
                         ┌────────────────────────────────────────────────────┐
                         │               Complete Protocol Runs               │
                         ├────────────────────────────────────────────────────┤
                         │                         success    fail     all    │
                         │                        --------  ------  ------    │
                         │    Attestation Tasks:                              │
                         │      Number               17399      38   17437    │
                         │      Percentage           99.8%    0.2%            │
                         │    Durations:                                      │
                         │      Average               8.8s    9.6s    8.8s    │
                         │      Shortest              1.9s    5.5s    1.9s    │
                         │      Longest              25.4s   14.5s   25.4s    │
                         │    Rates:                                          │
                         │      Per second             3.9     0.0     3.9    │
                         │      Per minute           233.9     0.5   234.5    │
                         │      Per hour             14037      31   14067    │
                         └────────────────────────────────────────────────────┘

```


## Advanced Configurations

Other deployments, beyond those described above, are possible:

- Deploy the PostgreSQL server on a system separate from the Keylime verifier to distribute load across multiple machines.

- Run the performance tests from multiple systems to maximise the amount of traffic hitting the Keylime verifier. The
  results from each separate execution of `./run_perf_tests` can be combined together by concatenating the appropriate
  `./results/*.jsonl` files. The combined file can then be processed with `./report_results <path_to_combined_file>`.