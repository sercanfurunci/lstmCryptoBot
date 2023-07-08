var chart = LightweightCharts.createChart(document.getElementById('chart'), {
	width: 1000,
	height: 500,
	layout: {
		background: {
			type: 'solid',
			color: '#000000',
		},
		textColor: 'rgba(255, 255, 255, 0.9)',
	},
	grid: {
		vertLines: {
			color: 'rgba(197, 203, 206, 0.5)',
		},
		horzLines: {
			color: 'rgba(197, 203, 206, 0.5)',
		},
	},
	crosshair: {
		mode: LightweightCharts.CrosshairMode.Normal,
	},
	rightPriceScale: {
		borderColor: 'rgba(197, 203, 206, 0.8)',
	},
	timeScale: {
		borderColor: 'rgba(197, 203, 206, 0.8)',
	},
  });
  
  var candleSeries = chart.addCandlestickSeries({
	upColor: 'rgba(255, 144, 0, 1)',
	downColor: '#000',
	borderDownColor: 'rgba(255, 144, 0, 1)',
	borderUpColor: 'rgba(255, 144, 0, 1)',
	wickDownColor: 'rgba(255, 144, 0, 1)',
	wickUpColor: 'rgba(255, 144, 0, 1)',
  });
  
  function updateChart(symbol) {
	fetch('http://127.0.0.1:5000/history?symbol=' + symbol)
	  .then((r) => r.json())
	  .then((response) => {
		console.log(response);
		candleSeries.setData(response);
	  });
  }
  
  updateChart('ETHUSDT'); // Initialize chart with BTCUSDT data
  
  var binanceSocket = null; // Initialize WebSocket variable
  
  document.getElementById('symbol').addEventListener('change', function() {
	if (binanceSocket) {
	  binanceSocket.close(); // Close the previous WebSocket connection
	}
  
	var selectedSymbol = this.value; // Get the selected symbol
	var socketURL = "wss://testnet.binance.vision/ws/" + selectedSymbol.toLowerCase() + "@kline_1m";
  
	binanceSocket = new WebSocket(socketURL); // Establish a new WebSocket connection
  
	binanceSocket.onmessage = function(event) {
	  var message = JSON.parse(event.data);
	  var candlestick = message.k;
  
	  candleSeries.update({
		time: candlestick.t / 1000,
		open: candlestick.o,
		high: candlestick.h,
		low: candlestick.l,
		close: candlestick.c
	  });
	};
  
	updateChart(selectedSymbol); // Update chart with historical data for the selected symbol
  });
  
  // Added code snippet
  document.getElementById('symbol').addEventListener('change', function() {
	var selectedSymbol = this.value; // Get the selected symbol
	chart.applyOptions({ title: selectedSymbol }); // Update chart title with selected symbol
  });
  