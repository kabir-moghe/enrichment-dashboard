import pandas as pd
import numpy as np
import requests
from tamr_unify_client import Client
from tamr_unify_client.auth import UsernamePasswordAuth
import json
import logging
import os
import time
tamr_log = logging.getLogger("tamr_unify_client")
tamr_log.setLevel(logging.WARNING)

def project_by_name(client, project_name): # function that outputs the project from inputted project name from login.html form

    for project in client.projects:
        if project.name == project_name:
            return project
    return None

def generate_export(project_name, tamr_client, path, input_dataset): # generates project with only relevant input data set records and matches

    logging.info(f'Identifying unified dataset for project {project_name}.')
    print(f'Identifying unified dataset for project {project_name}.')
    # Grab unified dataset name using project name
    project = project_by_name(tamr_client, project_name)

    print('Searching for {} records'.format(input_dataset))

    try:
        proj_id = project.resource_id
        unified_dataset = project.unified_dataset().name+"_dedup_published_clusters_with_data"
    except Exception as e:
        logging.error(f'Failed to identify unified dataset for project {project_name}. '
                      f'Ensure project name in config.json are correct. \n' + repr(str(e)))
        print(f'Failed to identify unified dataset for project {project_name}. '
                      f'Ensure project name in config.json are correct. \n' + repr(str(e)))
        return

    if not tamr_client.datasets.by_name(unified_dataset).status().is_streamable:
        logging.info(f'Refreshing unified dataset for project {project_name}.')
        print(f'Refreshing unified dataset for project {project_name}.')
        tamr_client.datasets.by_name(unified_dataset).refresh().succeeded()
    else:
        logging.info("%s can be streamed.", unified_dataset)
        print("%s can be streamed.", unified_dataset)

    # Grab unified dataset id
    datasetid = tamr_client.datasets.by_name(unified_dataset).relative_id.split('/')[1]
    record_generator = tamr_client.datasets.by_resource_id(datasetid).records() # creates iterable generator object with all the records
    records_as_strings = []
    records_as_list = []


    begin = time.time()

    persistent_ids = [] # creates list that will contain all the persistent IDs for the input_dataset records only
    num_records = 0 # sets tally that will count the number of total records just for reference (not used right now)

    for record in record_generator:
        num_records +=1 # adds 1 to number of records for each iteration

        if record['source_dataset_name'][0] == input_dataset: # if the record comes from the input dataset entered in authentication form...
            persistent_ids.append(record['persistentId']) # record's persistent ID is added to list, persistent_ids

    end = time.time()

    print(len(persistent_ids))

    print('Filtering: Took {} seconds'.format(str(end-begin)))

    print('Filtered Relevant Records')

    record_generator = tamr_client.datasets.by_resource_id(datasetid).records() # recreates generator for records

    begin = time.time()

    logging.info('Start converting generator object to json.')
    print('Start converting generator object to json.')
    with open(os.path.join(path, project_name+'.json'), 'w') as f:
        [f.write(json.dumps(record)+'\n') for record in record_generator if record['persistentId'] in persistent_ids]

        # creates a json object with only the records that have a persisent ID included in the list, persistent_ids
        # output will be a json object with only input dataset records and their matches
        # unmatched input data set records are still included at this point

    end = time.time()

    print('--> Json: Took {} seconds'.format(str(end-begin)))

    begin = time.time()

    logging.info("Converting json to pandas dataframe.") # converts json object to strings
    print("Converting json to pandas dataframe.")
    with open(os.path.join(path, project_name+'.json'), 'r') as f:
        for line in f:
            record = json.loads(line)
            records_as_strings.append(
                {key: "|".join([str(x).replace('\r', '') for x in val]) if (isinstance(val, list) & (val is not None))
                else val for key, val in record.items()}
            )
            records_as_list.append(record)

    df = pd.DataFrame(records_as_strings) # uses list of strings produced above to produce pandas dataframe for input data set records and matches

    end = time.time()

    print('--> DF: Took {} seconds'.format(str(end-begin)))

    datestring = time.strftime("%Y%m%d-%H%M%S")
    #schema_mapping_output = f'{filename}_{datestring}'
    return df, num_records
    #return unified_dataset, proj_id, schema_mapping_output

def data_cleaner(project_name, tamr_client, path, input_dataset):
    start = time.time()
    data, num_records = generate_export(project_name, tamr_client, path, input_dataset) # calls generate_export() with login form entries

    # Gets the pandas dataframe for input data set records and matches

    data = data[data['source_dataset_name'] != 'Dissolved_companies_Sodexo.csv'] # removes Dissolved companies records

    data.to_csv(project_name+'unfiltered_data3.csv') # data set has only records relating to input data set, but some input data set records are unmatched with companies house

    # saves this data set

    print('Cleaning Data') # begins removing unmatched input data set records

    # Fuctions that when applied to dataframe field for source data set, it will return a boolean value if the source data set is a specific data set

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

    # Applies functions above to create new columns with boolean values for what the source is

    data['companies_house?'] = data['source_dataset_name'].apply(dataname2)
    data['diss_companies?'] = data['source_dataset_name'].apply(dataname3)

    gb = data.groupby('persistentId')

    grouped = gb[['companies_house?', 'diss_companies?']].sum().reset_index()

    matched_ids = grouped[grouped['companies_house?'] == 1]['persistentId'].values # only gets persistent ids where there is no more than 1 Companies House match

    matched_data = data[data['persistentId'].isin(matched_ids)].reset_index(drop = True) # produces data set that only includes records for matched persistent IDs above

    matched_data = matched_data.fillna('--') # fills null values with '--'

    def not_supplied(value): # SIC Code column has both null values and "Not/None Supplied," creates function that will replace with '--'
        if value == 'Not Supplied' or value == 'None Supplied':
            return '--'
        else:
            return value

    matched_data['SICCode'] = matched_data['SICCode'].apply(not_supplied) # applies not_supplied() to replace remaining blank values as '--'

    matched_data.to_csv(project_name+'data3.csv') # saves the filtered data with only matched entities

    print('Done')
    final = time.time()

    print('Altogether, took {} seconds.'.format(final-start))
