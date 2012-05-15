var po = org.polymaps;
  
var map = po.map();

map.container(document.getElementById("map").appendChild(po.svg("svg")))
   .center({lat:31, lon:121})
   .zoomRange([0, 5])
   .zoom(2)
   .add(po.interact())
   .add(po.drag())
   .add(po.dblclick())
   .add(po.wheel())
   .add(po.hash());

map.add(
    po.image()
    .url("../tile/worldatlas/{Z}/{X}/{Y}.png")
    );

map.add(po.compass().pan("none"));
