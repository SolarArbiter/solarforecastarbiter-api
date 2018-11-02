# Solar Forecast Arbiter Dashboard
A simple tornado web app to demo dashboard design. There are lots of dead links and unresponsive buttons, that lead to pages/functionality that have yet to be decided on.

### Usage/ Installation
Install requirements with `pip install -r requirements.txt`

Run the script with `python serve.py`

Open [http://localhost:8080/tep](http://localhost:8080/tep) in a browser to view the dashboard.


#### Template Layout

base.html

 - Basic html structure, includes navbar, footer and head. Will conditionally include sidebar if `sidebar` variable is defined.

navbar.html
	
 - Includes header for logo/site name and main navigation.

head.html

 - The <head> html element.

sidebar.html

 - Left sidebar html to be included when the sidebar variable is defined either in a template or passed into the render() function.

footer.html

 - Site footer.

dash/

 - Dash includes secondary nav content and anything else that may be section-wide. 

data/  

 - Templates extending the `dash/data.html` dashboard.

org/

 - Templates extending the `dash/org.html` dashboard.
