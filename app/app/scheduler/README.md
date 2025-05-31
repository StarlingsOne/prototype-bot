### Rate Limits

As of 31 May 2025, the rate limits on flash 2.0 on the free account are:

```
Model	            RPM	TPM	        RPD
Gemini 2.0 Flash	15	1,000,000	1,500
```

* If our requests are set to a delay of every six seconds we're above the RPM of 4 seconds.
* If we have 60 new bots coming in, adding that to our current bot load which we'll say is 10, that's a total of 70.
* If we schedule 4 times per day, that's 280 requests per day on one market.
* Maximum bots on one market at 4 requests per day would be 375.
* Two markets maximum bots, 186
* Four markets maximum bots, 93
* Six markets maximum bots, 62.

So if we clamped down our bots to around 60 maximum, and kept our scheduling at 4 times per day we could have six different markets going.