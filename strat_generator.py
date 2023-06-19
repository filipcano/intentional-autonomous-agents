import re
import json

with open('params.json', 'r') as fp:
    params = json.load(fp)

# regex used to identify elements to change in original PRISM file
label_reg = re.compile("\/\/\s*{([a-zA-Z_]+)}")
strat_regex = "\[[\w-]+\]"
strategies_label = re.compile(strat_regex)

def process_params():
    if ("slippery_factor" not in params) or (params["slippery_factor"] == None) or (params["slippery_factor"] < 1):
        params["slippery_factor"] = 1
    params["acc0_prob"] = 1 - params["acc1_prob"] - params["acc2_prob"]
    params["brk0_prob"] = 1 - params["brk1_prob"] - params["brk2_prob"]
    params["noop1_prob"]= 1 - params["noop0_prob"]

    params["acc2_prob_s"] = round(params["acc2_prob"]/(2**params["slippery_factor"]-1),3)
    params["acc1_prob_s"] = round(params["acc1_prob"]/(2*params["slippery_factor"]-1),3)
    params["acc0_prob_s"] = 1 - params["acc1_prob_s"] - params["acc2_prob_s"]

    params["brk2_prob_s"] = round(params["brk2_prob"]/(2**params["slippery_factor"]-1),3)
    params["brk1_prob_s"] = round(params["brk1_prob"]/(2*params["slippery_factor"]-1),3)
    params["brk0_prob_s"] = 1 - params["brk1_prob_s"] - params["brk2_prob_s"]

    values_to_substitute = {}
    for actiontype in {'acc', 'brk'}:
        for slip in {'', '_s'}:
            for actionmagnitude in {0,1,2}:
                paramstr = f"{actiontype}{actionmagnitude}_prob{slip}"
                values_to_substitute[f"const double {paramstr}"] = "{:.3f}".format(params[paramstr])
    values_to_substitute["const double noop0_prob"] = "{:.3f}".format(params["noop0_prob"])
    values_to_substitute["const double noop1_prob"] = "{:.3f}".format(params["noop1_prob"])
    values_to_substitute["const double slippery_factor"] = "{:.3f}".format(params["slippery_factor"])
    values_to_substitute["formula is_slippery"] = params["slippery_range"]
    values_to_substitute["const double hesitant_factor"] = params["hesitant_factor"]
    params["values_to_substitute"] = values_to_substitute
    

def nice_parenthesis(instring):
    result = ""
    currenttab = 0
    for i in instring:
        
        if i == '(':
            currenttab += 1
            result += "(\n"
            for j in range(currenttab):
                result += "\t"
        elif i == ')':
            currenttab -= 1
            result += "\n"
            for j in range(currenttab):
                result += "\t"
            result += ")"
        elif (i != ' ') and (i != '\n'):
            result +=i
    return result

# generates template mdp file
def make_mdp(temp):
    file = open(temp, "r")
    lines = [line.strip() for line in file.readlines()]
    file.close()
    
    for i, line in enumerate(lines):
        label_match = label_reg.search(line)
        # compatible with "".format for changing variables from user input
        if label_match:
            start_ind = line.rfind("init") + 4 if "init" in line else line.rfind("=") + 1
            label = label_match.group(1)
            lines[i] = line[:start_ind] + " {{{}}};".format(label)
        strat_match = strategies_label.search(line)
        # resets car action labels to [], originally set to label for importing strategies
        if strat_match:
            lines[i] = re.sub(strat_regex, "[]", lines[i])

        # substitute values for acc,brk,nop probabilities and hesitant
        for key in params["values_to_substitute"]:
            if key in line:
                lines[i] = f"{key} = {params['values_to_substitute'][key]};"

    # rewrites lines into new file
    replaced = '\n'.join(lines)
    with open("temp/mdpgenerated.pm", "w") as f:
        f.write(replaced)

# generates DTMC files for a dictionary and file input
def make_dtmc(temp):
    with open('strategy.json') as fp:
        strategy = json.load(fp) ## this is a dict, keys are names of strategies

    if not params["use_visibility"]:
        for keystrat in strategy.keys():
            for keyaction in strategy[keystrat].keys():
                strategy[keystrat][keyaction] = strategy[keystrat][keyaction].replace(' ', '')
                strategy[keystrat][keyaction] = strategy[keystrat][keyaction].replace('seen_ped=0', 'false')
                strategy[keystrat][keyaction] = strategy[keystrat][keyaction].replace('seen_ped=1', 'true')
                strategy[keystrat][keyaction] = strategy[keystrat][keyaction].replace('visibility=0', 'false')
                strategy[keystrat][keyaction] = strategy[keystrat][keyaction].replace('visibility=1', 'true')

    for strat in strategy:
        with open(temp,'r') as fp:
            lines = [line.strip() for line in fp.readlines()]

        for i, line in enumerate(lines):
            # change file type from mdp to dtmc
            lines[i] = re.sub("mdp", "dtmc", lines[i])
            label_match = label_reg.search(line)
            # compatible with "".format for changing variables from user input
            if label_match:
                start_ind = line.rfind("init") + 4 if "init" in line else line.rfind("=") + 1
                label = label_match.group(1)
                lines[i] = line[:start_ind] + " {{{}}};".format(label)
            # substitute values for acc,brk,nop probabilities and hesitant
            for key in params["values_to_substitute"]:
                if key in line:
                    lines[i] = f"{key} = {params['values_to_substitute'][key]};"
            # finds strategy labels in PRISM file "[accelerate]..." and adds in corresponding guard
            strat_match = strategies_label.search(line)
            if strat_match:
                count_matches = 0 # makes sure only one key corresponds to the strategy
                for key in strategy[strat]: 
                    if key[1:-1] in strat_match.group(0):  # key[1:-1] to remove the initial and final square brackets
                        lines[i] = re.sub(strat_regex, f"[] {nice_parenthesis(strategy[strat][key])}  & ", lines[i]) 
                        count_matches += 1
                assert count_matches == 1, f"Strategy {strat_match.group(0)} is mathced with {count_matches} keys."
        replaced = '\n'.join(lines)
        with open(f"temp/dtmc_{strat}.pm", "w") as f:
            f.write(replaced)
        


def main(prism_file=""):
   

    # If prism file is given (executing normally should be prism_files/mdp.pm), use it. If empty, ask user for it.
    if prism_file == "":
        prism_file = input("Model file to convert to template: ") # use this to give manual input to convert 

    process_params()
    # makes ones mdp file

    make_mdp(prism_file)
    # makes one dtmc file per strategy listed in the json file
    make_dtmc(prism_file)

    # 
    # for strat in strategy:
    #     make_dtmc(strategy[strat], prism_file)

if __name__ == '__main__':
    main("prism_files/mdp_novis.pm")