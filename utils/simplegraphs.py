import Image, ImageDraw, StringIO

def sparkline(points, point=None, height=15, width=40, bubble=2, margin=5, scalefactor=4):    
    margin *= scalefactor
    height *= scalefactor
    width *= scalefactor
    bubble *= scalefactor
    
    im = Image.new("RGB", (width, height), 'white')
    draw = ImageDraw.Draw(im)
    height -= margin
    width -= margin
    
    mypoints = [(
      margin/2. + (width*(n/float(len(points)))),
      (height+margin/2.) - ((height*(float(i)/max(points))))
    ) for (n, i) in enumerate(points)]
    draw.line(mypoints, fill='#888888', width=1.5*scalefactor)
    
    if point:
        x, y = mypoints[points.index(float(point))]
        draw.ellipse((x-bubble, y-bubble, x+bubble, y+bubble), fill='#f55')        
    
    height += margin
    width += margin
    
    im.thumbnail((width/scalefactor, height/scalefactor), Image.ANTIALIAS)
    f = StringIO.StringIO()
    im.save(f, 'PNG')
    return f.getvalue()
