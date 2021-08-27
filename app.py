from flask import Flask, redirect, url_for, render_template, request
import pandas as pd
import viz
import login_data
import os
from os import path
from tamr_unify_client.auth import UsernamePasswordAuth
from tamr_unify_client import Client

app = Flask(__name__,template_folder='Templates')
app.secret_key = 'SECRET KEY'



@app.route('/', methods = ['GET', 'POST']) # Authentication page
def login():
    if request.method == "POST": # If the form has been filled out and submitted...

        protocol, host, port, username, password, project_name, input_dataset = request.form['protocol'], request.form['host'], request.form['port'], request.form['username'], request.form['password'], request.form['project_name'], request.form['input_dataset']

        # Gets protocol, host, port, username, password, project_name (i.e. Company_Enrichment_UK02.1), input_dataset (i.e. Salesforce Accouts) from form input

        with open('exported_data/'+project_name+'.json', 'w') as fp: # creates a blank json file that will contain data set grabbed from API (the data set for the inputted project_name)
            pass

        auth = UsernamePasswordAuth(username, password)
        client = Client(auth, host=host, port=port) # Uses username, password for authetication that goes into creatig Tamr Client

        def project_by_name(client, project_name): # Function that takes in project_name ad outputs project

            for project in client.projects:
                if project.name == project_name:
                    return project
            return None

        # Way of testing if authenticated or not by using project_by_name fuction
        #if the function works, the UsernamePasswordAuth succeeded. Otherwise, you are redirected to the login page

        try:
            project_by_name(client,project_name) # tries function to test auth

        except Exception as e: #

            return redirect(url_for('login')) #if fails, redirected to login page

        if path.exists(project_name+'data3.csv') == False:

            # checks to see if the data set for the project_name inputted already exists

            # If it does, it means the app doesn't eed to reconnect to API and go through process of grabbing data

            login_data.data_cleaner(project_name, client, 'exported_data/', input_dataset)

            # If data set doesn't exist, goes through line above to produce data using data_cleaner function from login_data.py

        misc_info = pd.DataFrame([project_name, input_dataset]).transpose().rename(columns = {0: 'Project Name', 1: 'Input'})

        # creates misc_info .csv that contains curret project name and target input dataset name
        # This file is used in other scripts to determine which data set to read in and which set of records to filter by

        misc_info.to_csv('misc_info.csv') # saves "miscellaneous information" .csv file

        return redirect(url_for('search')) # redirects you to search page
    else:
        return render_template('login.html') # If method is not post, meaning that the page is just loadig, the login page is rendered



@app.route("/search", methods=['GET', 'POST']) # Search/Entity-Level Page
def search():
    try: # if any errors, likely because misc_info.csv does not exist, so just redirects you to login
        project_name = pd.read_csv('misc_info.csv', index_col = 0)['Project Name'].iloc[0] # gets project name from misc_info.csv that will be used to read in correct data for viz.py scripts
        companies = viz.companies(project_name) # uses project name to create a list of all the matched entity names that will be used in a input/datalist attribute on specific entity search

        if path.exists(project_name+'data3.csv') == False: # If the data set for the project name doesn't exist, you are redirected to login
            return redirect(url_for('login'))
        else:
            if request.method == "POST": # if the data set does exist and information has been entered into search.html...

                # Checks to see if use case information does exist

                try:
                    selection = request.form["use_case"]  # grabs form field information for company
                    before, after, type, new_cols, improved_cols = viz.viz1(selection)

                    # Above outputs:
                    # row(s) for input_dataset
                    # row for matched_dataset
                    # type of enrichment (which includes the use case and the name)
                    # lists of new columns and improved columns for the selected entity: used to highlight new/improved information

                    return render_template("search2.html", project_name = project_name, new_cols = new_cols, improved_cols = improved_cols, companies = companies, before = [before.to_html(classes='data', header = True)], after = [after.to_html(classes='data', header = True)], type = type)

                    # renders "search2.html," which renders all the rows of information and highlighted additions/improvements for selected entity

                # If selected use case produces an error, then there are no example entities in the data set

                except Exception as e:
                    issue = 'No examples for this use case.' # outputs issue that will be displayed on search.html if no examples for use case produces error
                    return render_template("search.html", project_name = project_name, companies = companies, issue = issue)

            else: # If method is not post, then renders "search.html" with issue as a blank string rather than an error message for blank use case
                issue = ''
                return render_template('search.html', project_name = project_name, companies = companies, issue = issue)

    except Exception as e: # if any error, redirects you to login
        return redirect(url_for('login')) # redirects you to search page


@app.route('/metrics', methods = ['GET', 'POST']) # Metrics page for project as a whole
def metrics():
    try: # if any errors, likely because misc_info.csv does not exist, so just redirects you to login

        misc_info = pd.read_csv('misc_info.csv', index_col = 0) # reads in miscellaneous information from "misc_info.csv"

        project_name, input_dataset = misc_info['Project Name'][0], misc_info['Input'][0]

        # saves project_name and input_dataset from misc_info.csv, which are passed to functions in viz.py and functions for this route that will read and filter the correct data set

        if path.exists(project_name+'data3.csv') == False: # checks if data set for project_name exists (this methodology needs to be fixed)
            return redirect(url_for('login')) # if doesn't exist, takes you to login
        else:
            sic, matches, cols, with_status = viz.metrics() # calculates metrics from viz.py function, metrics()

            # outputs general information on SIC Codes, % Matches, New and Improved Columns, and Status information


            sic_before, sic_after = sic[0], sic[1] # % companies with SIC Codes before and after

            pct_matched, num_dedup, unmatched_before, total_after = matches # unpacks matches into % matched, number deduplicated, and entities before/after matching

            # Columns

            new_cols, improved_cols = cols # unpacks list of entirely new columns and improved columns

            num_new_cols = len(new_cols) # calculates the number of new columns from length of list of new columns
            num_improved_cols = len(improved_cols) # calculates the number of improved columns from length of list of improved columns

            # formatting message that will be displayed depending on if there are 1 or more new/improved records_as_list

            new_added_detail = '.'
            improved_added_detail = '.'

            # Don't want to say added details below if there were no new or improved columns, so leaves added information as a period above.

            if num_new_cols > 0:
                new_added_detail = ', each providing an additional layer of information.'
            if num_improved_cols > 0:
                improved_added_detail = ', adding improved information for entities across the fields.'

            # Entire lists of new/improved columns are too long if they're longer than 2 columns
            # Just shows a preview of new and improved columns if so:

            def sample_cols(cols):
                if len(cols) >2:
                    sample_cols = ', '.join(cols[:2])+'...'
                else:
                    sample_cols = ', '.join(cols)

                return sample_cols

            sample_new_cols = sample_cols(new_cols)
            sample_improved_cols = sample_cols(improved_cols)

            # Reads in unfiltered data that includes unmatched input records

            unfiltered_data = pd.read_csv(project_name+'unfiltered_data3.csv')

            # Reads in filtered data that only includes matched input records

            data = pd.read_csv(project_name+'data3.csv')

            unfiltered_dim_rows = len(unfiltered_data) # Calculates number of initial records before only including matched

            a_dim_rows = len(data) # Calculates number of only matched

            rows_removed = unfiltered_dim_rows - a_dim_rows # Calculates delta to show number removed (not currently included in metrics page but is there in case)

            dim_cols = len(data.columns) # gets the number of columns (not currently included in metrics page but is there in case)

            return render_template('metrics.html', input_dataset = input_dataset, dim_cols = dim_cols, unfiltered_dim_rows = unfiltered_dim_rows, rows_removed = rows_removed, a_dim_rows = a_dim_rows,
                                                   num_dedup = num_dedup, sic_after = sic_after, pct_matched = pct_matched, unmatched_before = unmatched_before, total_after = total_after,
                                                   new_cols = new_cols, improved_cols = improved_cols, num_new_cols = num_new_cols, num_improved_cols = num_improved_cols, sample_new_cols = sample_new_cols, sample_improved_cols = sample_improved_cols,
                                                   project_name = project_name, with_status = with_status, new_added_detail = new_added_detail, improved_added_detail = improved_added_detail)
    except Exception as e: # if any error, redirects you to login
        return redirect(url_for('login')) # redirects you to search page

if __name__ == '__main__':
    app.run(host='10.10.0.214', port=8050, debug=True)
