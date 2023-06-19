import pandas as pd
from tqdm import tqdm
import os, re, argparse, json, subprocess, random
import graph_generator



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', type=str, default='path_crash40_sample')
    parser.add_argument('--strategies', type=str, default='cautious,reckless,corrupt')
    args = parser.parse_args()
    folder_to_save = args.trace
    strategies_to_use = args.strategies


    infile = 'inputtotest.txt'
    with open(infile, 'r') as fp:
        inputsetup = fp.read().split(' ')
    inputsetup[1] = folder_to_save
    inputsetup[0] = strategies_to_use
    with open(infile, 'w') as fp:
        fp.write(' '.join(inputsetup))
    all_traces = [trace.split('.')[0] for trace in os.listdir('traces')]
    assert folder_to_save in all_traces, 'Trace not where supposed to be'


    slippery_ranges = [(40, 50), (30,55)] # range of street x where car is slippery (min, max)
    slippery_factors = [1,1.5,2,2.5] # between 1 and inf, inf max slipperyness
    hesitant_factors = [0.3, 0.6, 1] # between 0 and 1, 0 max hesitancy
    visibility_usages = [True, False]
    os.system(f"mkdir {folder_to_save}")

    all_counterfactuals_array = []

    #num of counterfactuals = 100
    slippery_range_inits = (20,40)
    slippery_range_ends = (45,65)
    slippery_factors = (1,4)
    hesitant_factors = (0.1, 0.9)
    n_counterfacts = 100
    for i in range(n_counterfacts):
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
        all_counterfactuals_array.append(cf)
        

    for cf in tqdm(all_counterfactuals_array):
        with open('params.json','r') as fp:
            params = json.load(fp)
        params["slippery_range"] = f"(car_x > {cf['slippery_range'][0]}) & (car_x < {cf['slippery_range'][1]})"
        params["slippery_factor"] = cf['slippery_factor']
        params["hesitant_factor"] = cf['hesitant_factor']
        params["use_visibility"] = cf['use_visibility']
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
        regex = re.compile('data_[a-z]*.csv')
        for datafile_name in os.listdir('temp'):
            if regex.search(datafile_name):
                os.system(f"cp temp/{datafile_name} {folder_to_save}/{graphs_added_name}_{datafile_name}")
    graph_generator.counterfactualScatterPlot(folder_to_save)

if __name__ == "__main__":
    main()