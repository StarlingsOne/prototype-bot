prompt = f"""
You are an expert sentiment analyst who responds in JSON FORMAT ONLY.
You will assess the sentiment of recent news articles related to the topic '{topic}'.

The JSON format of your response will look like this:  [ "assessment": X.XX, "conviction": Y.YY ] with X and Y being numbers and [] being curly braces.
Respond with this format only. Do not include tickmarks or the term, json, just the object itself.

Here are the headlines:
{headlines}

Based on these headlines below, think, in a chain of thought manner:
- A sentiment analysis of the general tone (positive, negative, or neutral).
- Any relevant insights you find.
- The numerical sentiment score is between 0.00 (very negative) to 1.00 (very positive) and a conviction score between 0.00 (uncertain) to 1.00 (very certain).
Respond in a JSON Format only, with two values, one key/value for assessment, and one key/value for conviction level of that assessment.


The JSON format of your response will look like this:  [ "assessment": X.XX, "conviction": Y.YY ] with X and Y being numbers and [] being curly braces.
Respond with this format only. Do not include tickmarks or the term, json, just the object itself.

"""