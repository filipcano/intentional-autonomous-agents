# Analyzing Intentional Behavior in Autonomous Agents Under Uncertainty

Accompaning repository to the paper "Analyzing Intentional Behavior in Autonomous Agents under Uncertainity", published at IJCAI 2023.

This is the code used to generate the results in Section 6 of the paper.

## Installation

Requirements
  - Python 3
  - pip install docker
  - Prism Model Checker

We use the prism model checker for path simulation. To install it, follow the instructions instructions given by the [website](https://www.prismmodelchecker.org/download.php).
Next, write the path to the Prism executable found in the bin directory into the `config.txt` file.

For Prism to work, it may be necessary to install the Java JDK if it is not already available. Whether Prism is working can be verified by running the `prism` executable found in the bin directory.

To answer the model checking queries we use a modified version of [TEMPEST](https://www.tempest-synthesis.org), which in turn is a fork of the [STORM](https://www.stormchecker.org/) model checker via [docker](https://www.docker.com/).
You can download the docker container with

```
docker pull lposch/tempest-devel-traces
```

## Project Structure
- **prism_files/**: contains the template prism files describing the MDP and also the properties to check.
  - *dtmc_props.props*: properties file for dtmc model.
  - *mdp_props.props*: properties file for mdp model.
  - *mdp.pm*: template mdp file.
  - *mdp_novis.pm*: template mdp file when no visibility block is considered.
- **traces/**: contains saved traces to study. Althought the trace evaluated is the same, because of implementation quirks, three copies are provided because it is used for three different results.
  - *path_crash40.txt*: the trace studied in the paper, used for rendering Figures 3 and 4.
  - *path_crash40_sample.txt*: the trace studied in the paper, used to run `counterfacutal_sample.py` and obtain Fig. 5.
  - *path_crash50.txt*: the trace studied in the paper, used to reproduce Tables 2 and 3.
- **path_crash40/**: folder containing the data to generate Figures 3 and 4. We include this here because Figures 3 and 4 correspond to scenarios that were hand-picked: the first one is the scenario under study, the second one is a concrete instance of a trace with high scope of agency.
- **temp/**: temp folder to house temporary data and files produced by the execution
- *config.txt*: contains the path to the prism executable. Only needed for path simalation.
- *counterfactual_evaluation_paper.py*: Script that implements the methodology described in Fig. 1 of the paper.
This is the main interface for the user.
- *counterfactual_sample.py*: Samples N=100 counterfactual traces for each policy $\pi_1, \pi_2, \pi_3$, to produce the scatter plot in Fig.5 of the paper.
- *graph_generator.py*: this file contains utilities to generate graphs of intention-quotient vs agency.
- *Graphs_notebook.ipynb*: jupyter notebook containing the implementation of the concrete graphs used in the paper. They differ from the graphs in `graph_generator.py` in aesthetic choices to make the presentation in one-column figures better to understand and more consistent with the rest of the paper style.
- *inputtotest.txt*: sample input given to `prism_runner.py`.
- *params.json*: parameter file for a trace. These parameters inform concrete values baked in the mdp by `prism_runner.py`. Each counterfactual trace is generated from a different instance of parameters.
- *README.md*: This ReadMe.
- *strat_generator.py*: Reads strategies from `strategy.json` and handles all the logic to bake them in the mdp files that will later be given to the model checker.
- *strategy.json*: Contains the strategies to use, in the paper called policies. The correspondance with policies in the paper is: {$\pi_1$: corrupt, $\pi_2$: reckless, $\pi_3$: cautious}.
- *trace_convert.py*: Handles the format conversion between traces as given by prism path simulation and
traces to be given as inputs to STORM.
Traces stored in the `traces/` directory are also in the same format as given by the prism path simulation.

## Running the code
The main script where all the calls to the model checker happen is `prism_runner.py`.
This script gets as input a set of strategies to test, trace to analyse plus initial conditions for the MDP.
Produces the mdp and dtmc files from the templates, baking in the initial state given as `inputtottest.txt` and the variations of environmental variables given in `params.json`.
Then calls STORM for each file, producing the model checking results and graphs. All produced data is dumped into the `temp/` directory.

The scripts `trace_convert.py` and `strat_generator.py` contain functionality auxiliar to `prism_runner.py`.

The methdology described in Figure 1 is implemented in `counterfactual_evaluation_paper.py`.
This script reads a policy and a trace, and produces a results table as in Table 2.
For analysing each concrete trace, `counterfactual_evaluation_paper.py` calls `prism_runner.py`.
All model checking data produced is store in a folder with the name of the trace.
We provide some of the data, the one used to make Figures 3 and 4, in one of these folders, `path_crash40`.

The script `counterfactual_sample.py` samples N=100 counterfactuals for the three policies considered,
as described in Figure 5.
As before, this script just handles the generation of concrete counterfactuals, while the analysis of each trace is done by calling `prism_runner.py`.

## Reproducing experimental results

### Tables 2 and 3

To reproduce the results in Table 2, run
```
python counterfactual_evaluation_paper.py --trace path_crash50.txt --strategy pi1
```
This script generates the table results in `table_results.csv`.

To reproduce the results in Table 3, run
```
python counterfactual_evaluation_paper.py --trace path_crash50.txt --strategy pi2
```
and
```
python counterfactual_evaluation_paper.py --trace path_crash50.txt --strategy pi3
```

Each command produces one results table `table_results.csv`. Table 3 summarizes the end state of the tables for the three strategies considered.

### Figure 5 (Scatter Plot)

To reproduce the results in Fig. 5, run
```
counterfactual_sample.py
```
This generates the results with counterfactual traces and their intention-quotient and scope of agency values in the folder `path_crash40_sample`.
The plot can be visualized in the notebook `Graphs_notebook.ipynb`.
