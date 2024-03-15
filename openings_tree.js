let network, nodes, edges, svgContext;


function loadFixedPositions() {
  let posDataString = localStorage.getItem('posData');
  if (posDataString) {
    posData = JSON.parse(posDataString);
    nodes.update(posData);
  }
}
function saveFixedPositions() {
  posData = []
  for (var node of nodes.get()) {
    if (node.fixed && node.moved) {
      let pos = network.getPosition(node.id);
      posData.push({
        "id": node.id,
        "x": pos.x,
        "y": pos.y,
        "fixed": true,
        "moved": true
      });
    }
  }
  localStorage.setItem('posData', JSON.stringify(posData));
}

window.addEventListener('load', (event) => {
    // create an array with nodes
    nodes = new vis.DataSet(NODES);
    // create an array with edges
    edges = new vis.DataSet(EDGES);
    // create a network
    var container = document.getElementById("network");
    var data = {
      nodes: nodes,
      edges: edges,
    };
    var options = {
      layout: {
        improvedLayout: false
      },
      physics: {
        solver: 'repulsion'
      },
      edges: {
        arrows: {
          to: {
            enabled: true
          }
        }
      },
      nodes: {
        font: {
          multi: "html"
        }
      }
    };
    network = new vis.Network(container, data, options);
    network.on("click", (e) => {
      for (var node of e.nodes) {
        nodes.update({ id: node, fixed: false });
      }
    })
    network.on("release", (e) => {
      for (var node of e.nodes) {
        nodes.update({ id: node, fixed: true, moved: true });
      }
    })
    var posButton = document.getElementById("save-pos-button");
    posButton.onclick = () => saveFixedPositions();
    loadFixedPositions();
})