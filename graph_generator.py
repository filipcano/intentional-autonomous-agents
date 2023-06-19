import pandas as pd
import numpy as np
from matplotlib import rc
from matplotlib import pyplot as plt
import json,os, re

COLORBOX = ['#ca06b8', '#ca9236', '#5132c7', '#3bf48c', '#bed092']
COLORS_BY_STRAT = {'cautious':'#89a348', 'reckless':'#bd2f9e', 'corrupt':'#1e4054'}
MARKERS_BY_STRAT = {'cautious': '^', 'reckless':'s', 'corrupt':'X'}

def getProbs(file):
    keys = []
    for key in file:
        keys.append(key['v'])
    # print(len(keys))
    return keys

def firstPlot(dfarray, states, state_ticks, state_labels, idx=0, strat_names=['strategy']):    
    # set up the plots
    fig, axs1 = plt.subplots(figsize = (7, 5))
    axs1.set_xlim(0,dfarray[0].shape[0])
    for spine in ['right', 'top']:
        axs1.spines[spine].set_visible(False)

    # plotting data
    axs1.fill_between(states, dfarray[0]['Pmin'], dfarray[0]['Pmax'], color = '#DBDBDB')
    axs1.plot(states, dfarray[0]['Pmin'], color = '#1a4314', marker = 'o', label = "Pmin", zorder=10, clip_on=False, alpha=0.5)
    axs1.plot(states, dfarray[0]['Pmax'], color = '#8d0000', marker = 'o', label = "Pmax", zorder=10, clip_on=False, alpha=0.5)

    # make a P line for each strategy chosen by user, new color, df will be new, new label
    for i in range(len(dfarray)):
        df = dfarray[i]
        strat_name = strat_names[i]
        colorused = COLORBOX[i%len(COLORBOX)] if strat_name not in COLORS_BY_STRAT else COLORS_BY_STRAT[strat_name]
        markerused = 'o' if strat_name not in MARKERS_BY_STRAT else MARKERS_BY_STRAT[strat_name]
        axs1.plot(states, df['P'], color = colorused, marker = markerused, label = strat_name, zorder=10, clip_on=False, alpha=0.5)


    axs1.vlines(idx,0,1)
    
    # labelling plot
    axs1.legend()
    axs1.set_xlabel('States')
    plt.xticks(state_ticks, state_labels)
    axs1.set_ylabel('Probability')
    plt.yticks([0, 0.5, 1.0], ['0','0.5', '1.0'])
    axs1.set_title('Raw probabilities')
    axs1.plot(1, 0, ">k", transform=axs1.get_yaxis_transform(), clip_on=False)
    
    # plt.tight_layout()
    axs1.margins(0)
    plt.savefig("temp/graph_left.png")

def secondPlot(dfarray, states, state_ticks, state_labels, idx=0, strat_names=['strategy']):    
    # set up the plots
    fig, axs2 = plt.subplots(figsize = (7, 5))
    axs2.set_xlim(0, dfarray[0].shape[0])
    for spine in ['right', 'top']:
        axs2.spines[spine].set_visible(False)
    roDiff = []
    roDiff = dfarray[0]['Pmax'] - dfarray[0]['Pmin']
    roDiffWidth = 0.25

    # making data for the plots
    for i in range(len(dfarray)):
        df = dfarray[i]
        strat_name = strat_names[i]
        ro1 = []
        ro1 = (df['P'] - df['Pmin'])/(df['Pmax'] - df['Pmin'])
        agency = df['Pmax'] - df['Pmin']
        agency_weights = agency/agency.sum()
        ro_weighted = ro1*agency_weights
        markerused = 'o' if strat_name not in MARKERS_BY_STRAT else MARKERS_BY_STRAT[strat_name]
        colorused = COLORBOX[i%len(COLORBOX)] if strat_name not in COLORS_BY_STRAT else COLORS_BY_STRAT[strat_name]
        axs2.plot(states, ro1, color = colorused, marker = markerused, label = f"rho {strat_name}", zorder=10, clip_on=False)
        axs2.axhline(y = ro_weighted.sum(), color = colorused, linestyle = '--', label = f"rho1 Mean = {ro_weighted.sum():.2f}")
    # plotting the data
    axs2.bar(states, roDiff, roDiffWidth, color = '#DBDBDB', edgecolor = '#BFBFBF',label=f"Acc. Agency = {roDiff.sum():.2f}")
    axs2.axvline(x = idx)
    axs2.legend()

    # labelling the plot
    axs2.set_xlabel('States')
    plt.xticks(state_ticks, state_labels)
    axs2.set_ylabel('Probability')
    plt.yticks([0,0.5, 1.0], ['0','0.5', '1.0'])
    axs2.plot(1, 0, ">k", transform=axs2.get_yaxis_transform(), clip_on=False)
    axs2.set_title('Relative intention')
        
    # axs2.margins(0)
    plt.savefig("temp/graph_right.png")

def parse_params_from_str(filename):
    parsed_params = {}
    slippery_range = re.compile('sliprange=[+-]?([0-9]*[.])?[0-9]+').search(filename).group().split('=')[-1].replace('.', ',')
    slippery_factor = re.compile('slipfact=[+-]?([0-9]*[.])?[0-9]+').search(filename).group().split('=')[-1]
    hesitant_factor = re.compile('hesfact=[+-]?([0-9]*[.])?[0-9]+').search(filename).group().split('=')[-1]
    use_visibility = re.compile('visblock=[a-zA-Z]*').search(filename).group().split('=')[-1]
    strategy = filename.split('_')[-1].split('.')[0]
    return slippery_range, slippery_factor, hesitant_factor, use_visibility, strategy

def counterfactualScatterPlot(folder_to_save, differentiate_visibility=False):
    counterfactual_df = pd.DataFrame(columns=['slippery_range', 'slippery_factor','hesitant_factor','use_visibility', 'strategy', 'agency','intention'],
                                index = range(len(os.listdir(folder_to_save))))
    curr_idx = 0
    for filename in os.listdir(folder_to_save):
        if filename.split('.')[-1] == 'csv':
            slippery_range, slippery_factor, hesitant_factor, use_visibility, strategy = parse_params_from_str(filename)
            df = pd.read_csv(f"{folder_to_save}/{filename}")
            df['agency'] = df.Pmax - df.Pmin
            df = df[df.agency > 0]
            df['intention'] = (df.P - df.Pmin)/df.agency
            df['agency_weights'] = df.agency/df.agency.sum()
            df['intention_weighted'] = df.intention*df.agency_weights

            intention = df.intention_weighted.sum()
            mean_agency = df.agency.mean()
            counterfactual_df.loc[curr_idx, :] = [slippery_range, slippery_factor, hesitant_factor, use_visibility,strategy,mean_agency,intention]
            curr_idx += 1
    counterfactual_df = counterfactual_df[counterfactual_df.index < curr_idx]
    
    counterfactual_df['color'] = "none"

    for i in counterfactual_df.index:
        counterfactual_df.loc[i,'color'] = COLORS_BY_STRAT[counterfactual_df.loc[i,'strategy']]
    
    counterfactual_df['agency_weights'] = counterfactual_df.agency/counterfactual_df.agency[counterfactual_df.strategy=='cautious'].sum()
    counterfactual_df['intention_weighted'] = counterfactual_df.agency_weights*counterfactual_df.intention
    visibilities = [{"True"}, {"False"}, {"True", "False"}] if differentiate_visibility else [{"True", "False"}]
    
    for visibility in visibilities:
        fig, axs1 = plt.subplots(figsize = (7, 5))

        for strat_name in counterfactual_df.strategy.unique():
            slice_df = counterfactual_df[counterfactual_df.strategy == strat_name]
            slice_df = slice_df[slice_df.use_visibility.isin(visibility)]
            weighted_intention = slice_df.intention_weighted.sum()
            axs1.scatter(x=slice_df.agency, y=slice_df.intention, 
                      c = slice_df.color.unique()[0], label = f"{strat_name}, {weighted_intention:.2f}")

        axs1.set_xlim(0,1)
        axs1.set_ylim(0,1)
        axs1.legend()
        axs1.set_xlabel('Agency')
        axs1.set_ylabel('Evidence for intention')
        axs1.set_title('Counterfactual evaluation')


        if differentiate_visibility:
            plt.savefig(f"{folder_to_save}/A_Counterfactual_Graph_withvis_{visibility}.pdf")
        else:
            plt.savefig(f"{folder_to_save}/A_Counterfactual_Graph.pdf")


def main(df1array, strat_names = ['strategy']):
    assert(len(df1array) == len(strat_names))
    for i in range(len(strat_names)):
        df1array[i].to_csv(f"temp/data_{strat_names[i]}.csv")
    # only use data until Pmax-Pmix < eps (data after this is useless)
    dfarray = []
    for i in range(len(df1array)):
        df1 = df1array[i]
        idx = df1.index[-1]
        eps = 0.005
        rodiff11 = df1['Pmax'] - df1['Pmin']

        while idx > 0:
            if np.abs(rodiff11[idx]) < eps:
                idx = idx -1 
            else:
                break
        # df = df1[0:idx]
        if idx + 3 < df1.index[-1]:
            df = df1[0:idx+3]
        else:
            df = df1 
        dfarray.append(df)
    
    # both graphs will plot to the same state tick
    state_labels = []
    states = []
    state_ticks = []
    for i in range(dfarray[0].shape[0]):
        states.append(i)
    for i in range(dfarray[0].shape[0]):
        if i*5 < dfarray[0].shape[0] -1:
            state_labels.append(f"s{5*i + 1}")
            state_ticks.append(5*i + 1)

    # plot styling
    plt.rcParams.update({'axes.labelsize' : 18, 'axes.titlesize': 18, 'font.family': 'serif'})

    firstPlot(dfarray, states, state_ticks, state_labels, idx, strat_names)
    secondPlot(dfarray, states, state_ticks, state_labels, idx, strat_names)

if __name__ == "__main__":
    df = pd.read_csv('temp/data.csv')
    main(df)