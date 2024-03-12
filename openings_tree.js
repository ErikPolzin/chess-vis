function loadFixedPositions(nodes) {
    let posDataString = Cookies.get('posData');
    if (posDataString) {
        posData = JSON.parse(posDataString);
        nodes.update(posData);
    }
}
function saveFixedPositions(network, nodes) {
    posData = []
    for (var node of nodes.get()) {
        if (node.fixed && node.moved) {
            let pos = network.getPosition(node.id);
            posData.push({
                "id": node.id,
                "x": pos.x,
                "y": pos.y,
                "fixed": true
            });
        }
    }
    Cookies.set('posData', JSON.stringify(posData));
}

window.onload = (e) => {
    // create an array with nodes
    var nodes = new vis.DataSet(NODES);
    // create an array with edges
    var edges = new vis.DataSet(EDGES);
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
      }
    };
    var network = new vis.Network(container, data, options);
    network.on("click", (e) => {
      for (var node of e.nodes) {
        nodes.update({ id: node, fixed: false });
      }
    })
    network.on("release", (e) => {
      for (var node of e.nodes) {
        console.log(nodes.get(node));
        nodes.update({ id: node, fixed: true, moved: true });
      }
    })
    var posButton = document.getElementById("save-pos-button");
    posButton.onclick = () => saveFixedPositions(network, nodes);
    loadFixedPositions(nodes);
}