# Tamr Enrichment-dashboard - Runs at 10.10.0.214:8050

The goal of this project is to create a dashboard that showcases the benefits of data enrichment, both on the individual/entity level and on the project level. The dashboard is built on Flask. 

# Authentication

Users must input their credentials along with the project name and input data set name they are searching for. The output is the data set for all the input data set records (matched and unmatched) that is used across the other pages. 

# Enriched Entity Search

The enriched entity search page allows a user to search for a specific use case of data enrichment for address attributes. The use cases are the following: 

1. Deduplication
2. Address entry
3. Address improvement

Users can also output a random example of enrichment or search for a specific example from a dropdown/datalist. The output displays the data from the input data set along with the data for the matched data set, with new and improved fields highlighted.

# Project-Level Metrics

This page displays metrics across the project as a whole. Overview information is shown in modular tiles, and when a user clicks on a tile, more information on the metric in the initial tile is shown. 

# Next steps:

1. Framework  
Flask has worked well, but visuals and interactivity will become more difficult to improve beyond a certain point. Next steps could mean shifting to REACT or another alternative framekwork.

2. Metrics
As of now, the metrics page has a fixed set of metrics that will be displayed. A next step could mean making it so that the metrics are calculated and shown depending on how positive they are.

3. Search 
3 use cases for enrichment are limited to address attributes. Though addresses are a good example, expanding to new attributes for use cases could show a broader range of benefits for enrichment.

4. Authentication & Login
Currently, you are by default taken to the login page, but if the matched data set exists, you can go to any other page and bypass authentication
Creating a session-based framework (through Flask or something else) could ease the process of ensuring authentication before going to other pages
This would also make multiple users using the app simultaneously easier.


