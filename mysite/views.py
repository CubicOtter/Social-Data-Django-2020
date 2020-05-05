from django.shortcuts import render, render_to_response
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components

def homepage(request):

    x = [1,2,3,4,5]
    y = [1,2,3,4,5]
    
    plot = figure(title = "Test graph", x_axis_label = "X-axis", y_axis_label = "Y-axis", plot_width = 400, plot_height = 400)
    plot.line(x,y,line_width = 2)
    script, div = components(plot)
    
    
    return render_to_response('pages/base.html', {"script":script,"div":div})