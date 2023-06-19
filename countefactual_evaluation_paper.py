import pandas as pd
from tqdm import tqdm
import os, re, argparse, json, subprocess, random, datetime
import graph_generator
import numpy as np

def analyse_one_trace(data_path):
    ## analyses one trace, returns rho and sigma for that trace
    df = pd.read_csv(data_path)
    df['agency'] = df.Pmax - df.Pmin
    df = df[df.agency > 0]
    df['intention'] = (df.P - df.Pmin)/df.agency

    df['agency_weights'] = df.agency/df.agency.sum()
    df['intention_weighted'] = df.intention*df.agency_weights

    intention = df.intention_weighted.sum()
    mean_agency = df.agency.mean()
    return intention, mean_agency
    



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', type=str, default='path_crash50')
    parser.add_argument('--strategy', type=str, default='pi1')
    args = parser.parse_args()
    folder_to_save = args.trace
    strategy = args.strategy
    # Translate the strategy to names given in the paper, in order to avoid biases in the reviewer against each strategy.
    strategy_paper_translate = {'pi1':'corrupt', 'pi2':'reckless', 'pi3':'cautious'}
    strategy = strategy_paper_translate[strategy]

    infile = 'inputtotest.txt'
    with open(infile, 'r') as fp:
        inputsetup = fp.read().split(' ')
    inputsetup[1] = folder_to_save
    inputsetup[0] = strategy
    with open(infile, 'w') as fp:
        fp.write(' '.join(inputsetup))
    all_traces = [trace.split('.')[0] for trace in os.listdir('traces')]
    assert folder_to_save in all_traces, 'Trace not where supposed to be'

    os.system(f"mkdir {folder_to_save}")

    slippery_range_inits = (20,40)
    slippery_range_ends = (45,65)
    slippery_factors = (1,4)
    hesitant_factors = (0.1, 0.9)

    target_rhoL = 0.25
    target_rhoU = 0.75
    target_sigma = 0.5
    N = 5

    rhos = []
    sigmas = []
    traces = []
    runtimes = []
    
    
    results_df = pd.DataFrame(columns=['Ntraces', 'rho', 'sigma', 'runtime'])
    for j in range(5):
        finished = False
        first_trace = True
        rhos = []
        sigmas = []
        traces = []
        runtimes = []
        auxtimestart = datetime.datetime.now()

        while not finished:
            safecount = 0
            i = 0
            while (i < N and safecount < 50*N):
                # print(f"i = {i}, safecount = {safecount}\n")
                safecount += 1
                if first_trace:
                    cf = {'slippery_range':(30,55),
                                'slippery_factor':2.5,
                                'hesitant_factor':0.5,
                                'use_visibility':True}
                    slippery_range = cf['slippery_range']
                    slippery_factor = cf['slippery_factor']
                    hesitant_factor = cf['hesitant_factor']
                    use_visibility = cf['use_visibility']
                else:
                    slippery_range_init = random.randrange(slippery_range_inits[0], slippery_range_inits[1])
                    slippery_range_end = random.randrange(slippery_range_ends[0], slippery_range_ends[1])
                    slippery_range = (slippery_range_init, slippery_range_end)
                    slippery_factor = random.uniform(slippery_factors[0], slippery_factors[1])
                    hesitant_factor = random.uniform(hesitant_factors[0], hesitant_factors[1])
                    use_visibility = False if random.randint(0,1) == 0 else True
                    cf = {'slippery_range':slippery_range,
                                    'slippery_factor':slippery_factor,
                                    'hesitant_factor':hesitant_factor,
                                    'use_visibility':use_visibility}
                with open('params.json','r') as fp:
                    params = json.load(fp)
                params["slippery_range"] = f"(car_x > {slippery_range[0]}) & (car_x < {slippery_range[1]})"
                params["slippery_factor"] = slippery_factor
                params["hesitant_factor"] = hesitant_factor
                params["use_visibility"] = use_visibility
                with open('params.json', 'w') as fp:
                    json.dump(params,fp,indent=2)
                outputfile = 'prism_output_file.txt'
                with open(outputfile, 'w') as foo:
                    with open(infile, 'r') as fin:
                        p = subprocess.Popen(['python3', 'prism_runner.py'], stdin=fin, stdout=foo, shell=False)
                        try:
                            p.wait(100)
                        except:
                            p.kill()
                            print(f"Had to kill prism runner after with 100 seconds with \n")
                            print(params)
                            print('\n---------\n')
                graphs_added_name = f"sliprange={cf['slippery_range'][0]}.{cf['slippery_range'][1]}_slipfact={cf['slippery_factor']}_hesfact={cf['hesitant_factor']}_visblock={cf['use_visibility']}"
                os.system(f"cp temp/graph_left.png {folder_to_save}/{graphs_added_name}_graph_left.png")
                os.system(f"cp temp/graph_right.png {folder_to_save}/{graphs_added_name}_graph_right.png")
                regex = re.compile(f'data_[a-z]*{strategy}.csv')
                for datafile_name in os.listdir('temp'):
                    if regex.search(datafile_name):
                        data_destiny = f'{folder_to_save}/{graphs_added_name}_{datafile_name}'
                        os.system(f"cp temp/{datafile_name} {data_destiny}")
                        rho, sigma = analyse_one_trace(data_destiny)
                        # print(rho, sigma, sigmas)
                        if first_trace:
                            sigmas.append(sigma)
                            rhos.append(rho)
                            traces.append(cf)
                        else:
                            if sigma >= np.mean(sigmas):
                                sigmas.append(sigma)
                                rhos.append(rho)
                                traces.append(cf)
                                i = i+1
                if first_trace:
                    first_trace = False
                    runtime = (datetime.datetime.now() - auxtimestart).total_seconds()
                    runtimes.append(runtime)
                    results_df = results_df.append({'Ntraces':len(traces), 'rho':np.mean(rhos), 'sigma':np.mean(sigmas), 'runtime':runtime}, ignore_index=True)
                    # print(f'summary of this batch: rho = {np.mean(rhos)}, sigma = {np.mean(sigmas)}, N_traces = {len(traces)}, runtime = {runtime}\n')

            if safecount == 50*N:
                print('\n\n Too many iterations \n\n')
            if np.mean(sigmas) > target_sigma:
                if np.mean(rhos) > target_rhoU:
                    finished = True
                    print("\nIntention found!\n")
                if np.mean(rhos) < target_rhoL:
                    finished=True
                    print('\n Non intention found!\n')
            runtime = (datetime.datetime.now() - auxtimestart).total_seconds()
            runtimes.append(runtime)
            results_df = results_df.append({'Ntraces':len(traces), 'rho':np.mean(rhos), 'sigma':np.mean(sigmas), 'runtime':runtime}, ignore_index=True)
            # print(f'summary of this batch: rho = {np.mean(rhos)}, sigma = {np.mean(sigmas)}, N_traces = {len(traces)}, runtime = {runtime}\n')

    results_df.to_csv(f'results_{strategy}.csv')
    results_df.Ntraces = results_df.Ntraces.astype(int)
    dfin = pd.DataFrame(columns=[results_df.Ntraces.unique()])
    for prop in ['rho', 'sigma', 'runtime']:
        for i in results_df.Ntraces.unique():
            dfin.loc[prop, i] = f"{results_df.groupby('Ntraces').mean().loc[i,prop]:.3f} ({results_df.groupby('Ntraces').std().loc[i,prop]:.3f})"
    
    dfin.to_csv('table_results.csv')

    


if __name__ == "__main__":
    main()