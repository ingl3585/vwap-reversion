// ResearchStrategy.cs

#region Using declarations
using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System.Globalization;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
using NinjaTrader.Data;
using NinjaTrader.Cbi;
using System.Windows.Media;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class ResearchStrategy : Strategy
    {
        #region Parameters
		
        [NinjaScriptProperty]
        [Display(Name = "Service URL", Order = 1, GroupName = "Parameters")]
        public string ServiceUrl { get; set; } = "http://127.0.0.1:8000/decide";

        [NinjaScriptProperty, Range(1, 100)]
        [Display(Name = "Max Position Size", Order = 2, GroupName = "Parameters")]
        public int MaxPositionSize { get; set; } = 2;

        [NinjaScriptProperty, Range(100, 10000)]
        [Display(Name = "HTTP Timeout (ms)", Order = 3, GroupName = "Parameters")]
        public int HttpTimeoutMilliseconds { get; set; } = 1000;

        [NinjaScriptProperty]
        [Display(Name = "Plot VWAP", Order = 4, GroupName = "Parameters")]
        public bool PlotVwap { get; set; } = true;
		
        #endregion
        #region Fields
		
        private const int MinimumRequestGapMilliseconds = 100;

        // Market data
        private double latestBidPrice;
        private double latestAskPrice;

        // HTTP throttle
        private DateTime lastHttpRequestAt = DateTime.MinValue;
        private bool isHttpRequestInFlight;

        // Session VWAP state
        private double cumulativePriceVolumeCommitted;
        private double cumulativeVolumeCommitted;
        private double sessionVwap;

        // Session tracking
        private SessionIterator sessionIterator;
        private string currentSessionKey;
        
		#endregion
        #region Lifecycle
		
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Research Strategy with HTTP decision engine";
                Name = "ResearchStrategy";
                Calculate = Calculate.OnEachTick;
                IsInstantiatedOnEachOptimizationIteration = false;
                BarsRequiredToTrade = 1;
                AddPlot(Brushes.Purple, "VWAP");
            }
            else if (State == State.DataLoaded)
            {
                sessionIterator = new SessionIterator(Bars);
                if (CurrentBar >= 0)
                {
                    sessionIterator.GetNextSession(Time[0], true);
                    currentSessionKey = sessionIterator.ActualSessionBegin.ToString("yyyy-MM-dd'T'HH:mm:ss");
                }
            }
        }
        
		#endregion
        #region OnBarUpdate / OnMarketData
		
        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0) return;

            if (Bars.IsFirstBarOfSession && IsFirstTickOfBar)
            {
                cumulativePriceVolumeCommitted = 0.0;
                cumulativeVolumeCommitted = 0.0;

                sessionIterator.GetNextSession(Time[0], true);
                currentSessionKey = sessionIterator.ActualSessionBegin.ToString("yyyy-MM-dd'T'HH:mm:ss");
            }

            if (IsFirstTickOfBar && CurrentBar > 0)
            {
                double previousTypicalPrice = (High[1] + Low[1] + Close[1]) / 3.0;
                double previousVolume = Math.Max(0.0, Volume[1]);
                cumulativePriceVolumeCommitted += previousTypicalPrice * previousVolume;
                cumulativeVolumeCommitted += previousVolume;
            }

            double currentVolume = Math.Max(0.0, Volume[0]);
            double currentTypicalPrice = (High[0] + Low[0] + Close[0]) / 3.0;

            double numerator = cumulativePriceVolumeCommitted + currentTypicalPrice * currentVolume;
            double denominator = cumulativeVolumeCommitted + currentVolume;

            sessionVwap = denominator > 0 ? numerator / denominator : 0.0;

            if (PlotVwap && sessionVwap > 0)
                Values[0][0] = sessionVwap;
        }

        protected override void OnMarketData(MarketDataEventArgs e)
        {
            if (e.MarketDataType == MarketDataType.Bid) { latestBidPrice = e.Price; return; }
            if (e.MarketDataType == MarketDataType.Ask) { latestAskPrice = e.Price; return; }
            if (e.MarketDataType != MarketDataType.Last || latestBidPrice <= 0 || latestAskPrice <= 0) return;

            if (isHttpRequestInFlight || (DateTime.Now - lastHttpRequestAt).TotalMilliseconds < MinimumRequestGapMilliseconds) return;

            _ = Task.Run(() => SendDecisionRequest(e));
        }
        
		#endregion
        #region Networking / Decisions
		
        private async Task SendDecisionRequest(MarketDataEventArgs e)
        {
            if (isHttpRequestInFlight) return;
            isHttpRequestInFlight = true;
            lastHttpRequestAt = DateTime.Now;

            try
            {
                string payload = BuildJsonRequest(e);
                string response = await PostJsonAsync(ServiceUrl, payload);
                await Dispatcher.InvokeAsync(() => ProcessResponse(response));
            }
            catch (Exception ex)
            {
                Print($"Request error: {ex.Message}");
            }
            finally
            {
                isHttpRequestInFlight = false;
            }
        }

        private void ProcessResponse(string response)
        {
            try
            {
                string action = ExtractJsonString(response, "action");
                if (string.IsNullOrEmpty(action)) return;

                switch (action.ToLowerInvariant())
                {
                    case "flatten":
                        if (Position.MarketPosition == MarketPosition.Long) ExitLong();
                        else if (Position.MarketPosition == MarketPosition.Short) ExitShort();
                        break;

                    case "place":
                        PlaceOrder(response);
                        break;
                }
            }
            catch (Exception ex)
            {
                Print($"Response error: {ex.Message}");
            }
        }

        private void PlaceOrder(string response)
        {
            string side = ExtractJsonString(response, "side")?.ToLowerInvariant();
            string orderType = ExtractJsonString(response, "orderType")?.ToLowerInvariant();
            int quantity = ExtractJsonInt(response, "quantity");
            double limitPrice = ExtractJsonDouble(response, "limitPrice");

            if (string.IsNullOrEmpty(side) || quantity <= 0) return;

            int projectedPosition = Position.Quantity + (side == "buy" ? quantity : -quantity);
            if (Math.Abs(projectedPosition) > MaxPositionSize) return;

            bool isBuy = side == "buy";
            if (orderType == "market")
            {
                if (isBuy) EnterLong(quantity, "Signal");
                else       EnterShort(quantity, "Signal");
            }
            else
            {
                double price = limitPrice > 0 ? limitPrice : (latestBidPrice + latestAskPrice) / 2.0;
                price = Instrument.MasterInstrument.RoundToTickSize(price);
                if (isBuy) EnterLongLimit(quantity, price, "Signal");
                else       EnterShortLimit(quantity, price, "Signal");
            }
        }
       
		#endregion
        #region JSON Helpers
		
        private string BuildJsonRequest(MarketDataEventArgs e)
        {
            string sessionDateString =
                (!string.IsNullOrEmpty(currentSessionKey) && currentSessionKey.Contains("T"))
                    ? currentSessionKey.Split('T')[0]
                    : e.Time.Date.ToString("yyyy-MM-dd");

            var sb = new StringBuilder(320);
            sb.Append('{');
            AddJsonField(sb, "symbolName", Instrument.FullName); sb.Append(',');
            AddJsonField(sb, "timestampIso", e.Time.ToUniversalTime().ToString("o")); sb.Append(',');
            AddJsonField(sb, "lastPrice", e.Price); sb.Append(',');
            AddJsonField(sb, "lastSize", (long)e.Volume); sb.Append(',');
            AddJsonField(sb, "bidPrice", latestBidPrice); sb.Append(',');
            AddJsonField(sb, "askPrice", latestAskPrice); sb.Append(',');
            AddJsonField(sb, "positionQty", Position.Quantity); sb.Append(',');
            AddJsonField(sb, "sessionDate", sessionDateString); sb.Append(',');
            AddJsonField(sb, "vwap", sessionVwap);
            sb.Append('}');
            return sb.ToString();
        }

        private async Task<string> PostJsonAsync(string url, string json)
        {
            var request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = "POST";
            request.ContentType = "application/json";
            request.Timeout = request.ReadWriteTimeout = HttpTimeoutMilliseconds;

            using (var writer = new StreamWriter(await request.GetRequestStreamAsync()))
                await writer.WriteAsync(json);

            try
            {
                using (var response = (HttpWebResponse)await request.GetResponseAsync())
                using (var reader = new StreamReader(response.GetResponseStream()))
                    return await reader.ReadToEndAsync();
            }
            catch (WebException wex)
            {
                string body = "";
                if (wex.Response is HttpWebResponse resp && resp.GetResponseStream() != null)
                {
                    using (var rdr = new StreamReader(resp.GetResponseStream()))
                        body = await rdr.ReadToEndAsync();
                }
                throw new Exception($"HTTP {(wex.Response as HttpWebResponse)?.StatusCode}: {body}");
            }
        }

        private void AddJsonField(StringBuilder sb, string key, string value)
        {
            sb.Append($"\"{key}\":\"{value?.Replace("\\", "\\\\").Replace("\"", "\\\"")}\"");
        }

        private void AddJsonField(StringBuilder sb, string key, double value)
            => sb.Append($"\"{key}\":{value.ToString("G17", CultureInfo.InvariantCulture)}");

        private void AddJsonField(StringBuilder sb, string key, long value)
            => sb.Append($"\"{key}\":{value.ToString(CultureInfo.InvariantCulture)}");

        private string ExtractJsonString(string json, string key)
        {
            int start = json.IndexOf($"\"{key}\":");
            if (start < 0) return null;
            start = json.IndexOf(':', start) + 1;
            while (start < json.Length && char.IsWhiteSpace(json[start])) start++;
            if (start >= json.Length || json[start] != '"') return null;

            int end = ++start;
            var result = new StringBuilder();
            while (end < json.Length && json[end] != '"')
            {
                if (json[end] == '\\' && end + 1 < json.Length) result.Append(json[++end]);
                else result.Append(json[end]);
                end++;
            }
            return result.ToString();
        }

        private int ExtractJsonInt(string json, string key)
        {
            int start = json.IndexOf($"\"{key}\":");
            if (start < 0) return 0;
            start = json.IndexOf(':', start) + 1;
            int end = start;
            while (end < json.Length && (char.IsDigit(json[end]) || json[end] == '-')) end++;
            string s = json.Substring(start, end - start).Trim();
            return int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out int result) ? result : 0;
        }

        private double ExtractJsonDouble(string json, string key)
        {
            int start = json.IndexOf($"\"{key}\":");
            if (start < 0) return 0.0;
            start = json.IndexOf(':', start) + 1;
            int end = start;
            while (end < json.Length &&
                   (char.IsDigit(json[end]) || json[end] == '-' || json[end] == '.' || json[end] == 'e' || json[end] == 'E'))
                end++;
            string s = json.Substring(start, end - start).Trim();
            return double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out double result) ? result : 0.0;
        }
        #endregion
    }
}
