# Solar Forecast Arbiter Dashboard
## Architecture
serve.py is a simple tornado server to use while working on the site. use `python serve.py` to run.


base.html
	Basic html structure, includes navbar, footer and head. Will conditionally include sidebar if `sidebar` variable is defined.
navbar.html
	Includes header for logo/site name and main navigation.
head.html
	The <head> html element.
sidebar.html
	Left sidebar html to be included when the sidebar variable is defined either in a template or passed into the render() function.
footer.html
	Site footer.
dash/
	Dash includes secondary nav content and anything else that may be section-wide. 
data/  
	Templates extending the `dash/data.html` dashboard.
org/
	Templates extending the `dash/org.html` dashboard.
