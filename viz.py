import random
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly
import plotly.express as px
import json

# HIGH LEVEL METRICS

def clean_name(name_list): # function that outputs cleaned, split, and capitalized names for list of columns that are usually lower case and split by underscores

    clean_names = []

    for name in name_list:

        split_name = name.split('_')

        # If an acronym is part of a name, function checks for two capital letters in a row and keeps the name of the column intact

        caps = 0

        for char in name:
            if char.isupper():
                caps+=1
            else:
                caps = 0
            if caps ==2:
                break
        if caps == 2:
            clean_names.append(name)

        elif len(split_name) > 1:

            name_pieces = [piece.title() for piece in split_name]
            clean_names.append(' '.join(name_pieces))

        else:
            clean_names.append(name.title())

    return clean_names # returns clean names for the entire inputted list of column names

def metrics():

    project_name, input_dataset = pd.read_csv('misc_info.csv')['Project Name'].iloc[0], pd.read_csv('misc_info.csv')['Input'].iloc[0]

    # gets project name and input data set name from misc_info.csv, which are used to determine which data set to read, which records to filter by, and what names to give visualizations that are saved

    matplotlib.use('Agg') # allows for passing and saving of matplotlib graphs in web framework

    # Fuctions that when applied to dataframe field for source data set, it will return a boolean value if the source data set is a specific data set

    def gb(df):
        def dataname1(name):
            if name == input_dataset:
                return True
            else:
                return False

        def dataname2(name):
            if name == 'companies-house-and-uk-establishments':
                return True
            else:
                return False

        def dataname3(name):
            if name == 'Dissolved_companies_Sodexo.csv':
                return True
            else:
                return False

        # Has SIC Function

        def sic(value):
            if type(value) == str:
                if value == 'None Supplied':
                    return False
                else:
                    return True
            else:
                return False

        def status(value):
            if type(value) == str:
                if value != '--':
                    return True
                else:
                    return False

            else:
                return False
        # Applies functions above to create new columns with boolean values for what the source is

        df[input_dataset+'?'] = df['source_dataset_name'].apply(dataname1)
        df['companies_house?'] = df['source_dataset_name'].apply(dataname2)
        df['diss_companies?'] = df['source_dataset_name'].apply(dataname3)
        df['has_sic?'] = df['SICCode'].apply(sic)
        df['has_status?'] = df['company_status'].apply(status)


        gb = df.groupby('persistentId')

        # Creates dataframe showing the tally for each data source for each 'persistentId' from groupby object above

        grouped = gb[[input_dataset+'?', 'companies_house?', 'diss_companies?', 'has_sic?','has_status?']].sum().reset_index()

        return grouped

    unfiltered_data = pd.read_csv(project_name + 'unfiltered_data3.csv', index_col = 0) # reads in unfiltered_data for a project (only input data set and compannies house matches, but some input data set records are unmatched)
    data = pd.read_csv(project_name + 'data3.csv', index_col = 0) # reads in filtered_data for a project (only matched entities)

    grouped = gb(unfiltered_data)

    filtered_grouped = gb(data)

    # Calculates SIC Code Metrics
    def calc_sic():
        #creates df with matches only (where both input_dataset? and companies house? are both ≥1)
        sic_by_source = unfiltered_data.groupby('source_dataset_name')['has_sic?'].sum()

        has_before = round(sic_by_source[input_dataset]/data['persistentId'].nunique()*100) # percent of entities with input data set records that have SIC Code
        has_after = round(sic_by_source['companies-house-and-uk-establishments']/data['persistentId'].nunique()*100) # percent of entities with companies house records that have SIC Code

        plt.figure()

        # Pie Chart for % with SIC After Enrichment

        plt.pie((has_after,(100-has_after)), startangle=90, colors = ['#AEF5DC','#EFADAA'],shadow=True, wedgeprops={'linewidth': 0})

        plt.savefig('static/'+project_name+'sic_after.png', transparent=True, bbox_inches='tight') # saves figure to static directory

        plt.close()

        # creates interactve bar graph top SIC Codes

        top_sic_df = pd.DataFrame(data[data['SICCode'] != '--']['SICCode'].value_counts().head(5)).reset_index().rename(columns = {'index': 'SICCode', 'SICCode': 'Count'})

        top_sic_df['SICCode'] = top_sic_df['SICCode'].apply(lambda value: value.split(' - ')[-1])

        config = {'displayModeBar': False}

        fig = px.bar(top_sic_df, y="SICCode", x="Count", orientation= 'h', color = 'SICCode')
        fig.update_layout(margin = {'r': 0, 't': 0, 'l': 0, 'b': 0}, font_family = "Source Sans Pro", hoverlabel_font_family = "Source Sans Pro", plot_bgcolor="rgba(0, 0, 0, 0)", paper_bgcolor='rgba(0, 0, 0, 0)', width = 550, showlegend = True,
        hoverlabel_bgcolor='#FFFFFF', hoverlabel_bordercolor = '#FFFFFF', hoverlabel_font_color='#000000'
        )

        fig.update_layout(legend=dict(
            yanchor="top",
            y=-0.2,
            xanchor="left",
            x=0.3
        ))

        fig.update_yaxes(visible=True, showticklabels=False)

        fig.write_html('Templates/'+project_name+'top_sic.html', full_html = False, config = config)

        return ['{}% with SIC'.format(has_before), '{}% with SIC'.format(has_after)]

    # Calculates % Matched Metrics
    def calc_match_pcts():

        # Number of total records before removing unmatched records

        unmatched_before = len(grouped)

        total_after = len(filtered_grouped) # only matched entities

        pct_matched_comp = round(total_after/len(grouped)*100)

        # Creates pie chart for % matched

        plt.figure()

        plt.pie((pct_matched_comp,(100-pct_matched_comp)), startangle=90, colors = ['#FFE579','#BDE3FF'], shadow=True, wedgeprops={'linewidth': 0})

        plt.savefig('static/'+project_name+'matched.png', transparent=True, bbox_inches='tight')

        plt.close()

        # Calculates Deduplication Metrics

        def calc_dedup():

            # Number from Input Accounts
            num_before= sum(unfiltered_data['source_dataset_name'] == input_dataset)

            data_input = grouped[grouped[input_dataset+'?']!=0] # when the sum of 'True's for a 'persistentId' is 0, the source data does not come from whatever data set is not shown

            num_after = len(data_input) # the number of companies that are from Input after Companies House enrichment

            if num_after == 1:
                return '{} Record Deduplicated'.format(num_before-num_after)
            else:
                return '{} Records Deduplicated'.format(num_before-num_after)

        dedup = calc_dedup()

        return '{}% Matched'.format(pct_matched_comp), dedup, unmatched_before, total_after

    # Finds new and improved columns through enrichment

    def empty_improved():
        empty = [] # list that will contain all the initially empty columns that were added through enrichment
        improved = [] # list that will contain all the columns improved through enrichment

        for col in unfiltered_data.columns:
            bf = sum(unfiltered_data[unfiltered_data['source_dataset_name'] == input_dataset][col].isna() == False)
            ch = sum(unfiltered_data[unfiltered_data['source_dataset_name'] == 'companies-house-and-uk-establishments'][col].isna() == False)

            if ch > bf:
                if bf == 0: # if the number of records before are 0, then the column is empty
                    empty.append(col)
                else: # if the number of records before is not empty but is still less than the number after, then the column is improved
                    improved.append(col)

         # cleans the names of the columns using the clean_name() function

        empty = clean_name(empty)
        improved = clean_name(improved)

        return empty, improved

    # Calculates the status metrics for the status field

    def calc_status():

        with_status = filtered_grouped[filtered_grouped['has_status?']!= 0]

        pct_status = round(len(with_status)/len(filtered_grouped) * 100)

        # pie chart for percent with status post enrichment

        plt.figure()

        plt.pie((pct_status,(100-pct_status)), startangle=90, colors = ['#57799A','#EFC9AA'], shadow=True, wedgeprops={'linewidth': 0})

        plt.savefig('static/'+project_name+'status.png', transparent=True, bbox_inches='tight')

        plt.close()

        top_status = pd.DataFrame(data[data['company_status'] != '--']['company_status'].value_counts()).reset_index().rename(columns = {'index': 'Status', 'company_status': 'Count'})

        # interactive bar chart for the top statuses

        config = {'displayModeBar': False}

        fig = px.bar(top_status, y="Status", x="Count", orientation= 'h', color = 'Status')
        fig.update_layout(margin = {'r': 0, 't': 0, 'l': 0, 'b': 0}, font_family = "Source Sans Pro", hoverlabel_font_family = "Source Sans Pro", plot_bgcolor="rgba(0, 0, 0, 0)", paper_bgcolor='rgba(0, 0, 0, 0)', width = 550, showlegend = True,
        hoverlabel_bgcolor='#FFFFFF', hoverlabel_bordercolor = '#FFFFFF', hoverlabel_font_color='#000000'
        )

        fig.update_layout(legend=dict(
            yanchor="top",
            y=-0.2,
            xanchor="left",
            x=0.3
        ))

        fig.update_yaxes(visible=True, showticklabels=False)

        fig.write_html('Templates/'+project_name+'top_status.html', full_html = False, config = config)

        return '{}% with Status'.format(pct_status)

    return calc_sic(), calc_match_pcts(), empty_improved(), calc_status()

# LOW LEVEL/SEARCH

def companies(project_name):

    # generates the list of matched companies/entities for a given project name

    data3 = pd.read_csv(project_name +'data3.csv', index_col = 0)
    return list(data3['clusterName'].unique())

def viz1(selection):

    project_name, input_dataset = pd.read_csv('misc_info.csv')['Project Name'].iloc[0], pd.read_csv('misc_info.csv')['Input'].iloc[0]

    # reads in project name and input data set name from misc_info.csv

    data3 = pd.read_csv(project_name + 'data3.csv', index_col = 0)
    data3 = data3.fillna('--') # in case there are still null values ot replaced

    if selection != 'random' and selection != 'deduplication' and selection != 'address_entry' and selection != 'address_improvement':

        # specific company being entered, not use case or random

        sample_company = data3[data3['clusterName'] == selection]['persistentId'].iloc[0]
        type = selection # the title of the data shown on the search2.html page
    else:

        if selection == 'random':

            # random example

            sample_company = random.choice(data3['persistentId'].unique())
            name = data3[data3['persistentId'] == sample_company]['clusterName'].iloc[0]
            type = 'Random Entity - {}'.format(name) # the title of the data shown on the search2.html page

        elif selection == 'deduplication':

            # deduplication example

            def dataname1(name):
                if name == input_dataset:
                    return True
                else:
                    return False
            data3[input_dataset+'?'] = data3['source_dataset_name'].apply(dataname1)
            record_tally = pd.DataFrame(data3.groupby('persistentId')[input_dataset+'?'].sum()).reset_index()
            deduplication_ids = record_tally[record_tally[input_dataset+'?'] > 1]['persistentId'].values # wherever the number of input dataset records is more than 1, example of deduplication

            sample_company = random.choice(deduplication_ids)
            name = data3[data3['persistentId'] == sample_company]['clusterName'].iloc[0]
            type = 'Deduplication - {}'.format(name) # the title of the data shown on the search2.html page

        elif selection == 'address_entry':

            # address entry example

            empty_address_ids = data3[(data3['source_dataset_name'] == input_dataset) & (data3['address_line_1'] == '--') & (data3['address_line_2'] == '--') & (data3['city'] == '--') & (data3['postal_code'] == '--')]['persistentId'].values
            sample_company = random.choice(empty_address_ids)
            name = data3[data3['persistentId'] == sample_company]['clusterName'].iloc[0]
            type = 'Address Entry - {}'.format(name) # the title of the data shown on the search2.html page
        else:

            # address improvement example

            filled_address = data3[data3['full_address'] != '--']

            improved_address_ids = []

            for p_id in filled_address['persistentId'].unique():
                id_data = filled_address[filled_address['persistentId'] == p_id]
                sf_section = [address.lower() for address in id_data[id_data['source_dataset_name'] == input_dataset]['full_address'].unique()]
                ch_section = [address.lower() for address in id_data[id_data['source_dataset_name'] == 'companies-house-and-uk-establishments']['full_address'].unique()][0]

                if 'united kingdom' not in sf_section and ch_section != 'united kingdom' and ch_section not in sf_section:
                    improved_address_ids.append(p_id)

            sample_company = random.choice(improved_address_ids)
            name = data3[data3['persistentId'] == sample_company]['clusterName'].iloc[0]
            type = 'Address Improvement - {}'.format(name) # the title of the data shown on the search2.html page

    sample_info = data3[data3['persistentId'] == sample_company][['source_dataset_name','company_name', 'full_address', 'address_line_1', 'address_line_2', 'city','postal_code', 'SICCode']].rename(columns = {'source_dataset_name': 'Dataset'}).sort_values(by = 'Dataset').reset_index(drop = True)

    before = sample_info[sample_info['Dataset'] == input_dataset].reset_index(drop = True) # input dataset records
    after = sample_info[sample_info['Dataset'] != input_dataset].reset_index(drop = True) # companies house records

    relevant_cols = ['company_name', 'full_address', 'address_line_1', 'address_line_2', 'city','postal_code', 'SICCode']

    new_cols = [] # list that will allow for the highlighting of new columns. Ultimately passed to javascript for highlighting
    improved_cols = [] # list that will allow for the highlighting of improved columns. Ultimately passed to javascript for highlighting

    for col in relevant_cols:

        bval = before[col].iloc[0]
        aval = after[col].iloc[0]

        if bval == '--' and aval != '--':
            new_cols.append(aval)
        elif bval != '--' and aval !='--':
            if bval.lower() != aval.lower():
                improved_cols.append(aval)

    before.columns, after.columns = clean_name(before.columns), clean_name(after.columns)

    before, after = before.replace('--', ''), after.replace('--','') # replaces dashes with blak string for better appearace

    return before, after, type, new_cols, improved_cols # random example of before and after enrichment for company name and address; can change "full_address" to something else to highlight another field
