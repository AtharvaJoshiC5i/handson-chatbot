"""Natural-language evaluation questions for Phase 1 usage intelligence."""

from __future__ import annotations


PHASE1_USAGE_EVALUATION_QUESTIONS = [
    # ========================================================
    # CURRENT DATA USAGE
    # ========================================================
    {
        "question": "How much data have I used this month?",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
    },
    {
        "question": "How many GB have I used?",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
    },
    {
        "question": "What's my internet usage?",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
    },
    {
        "question": "Show my September data usage.",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
        "month": 9,
    },

    # ========================================================
    # REMAINING DATA
    # ========================================================
    {
        "question": "How much data do I have left?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "DATA",
    },
    {
        "question": "What's my remaining data allowance?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "DATA",
    },
    {
        "question": "What's my data balance?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "DATA",
    },
    {
        "question": "How many GB are still available?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "DATA",
    },

    # ========================================================
    # DATA PERCENTAGE
    # ========================================================
    {
        "question": "What percentage of my data have I used?",
        "intent": "GET_USAGE_PERCENTAGE",
        "usage_type": "DATA",
        "percentage_type": "CONSUMED",
    },
    {
        "question": "How much of my data allowance have I consumed?",
        "intent": "GET_USAGE_PERCENTAGE",
        "usage_type": "DATA",
        "percentage_type": "CONSUMED",
    },
    {
        "question": "What percentage of my data is remaining?",
        "intent": "GET_USAGE_PERCENTAGE",
        "usage_type": "DATA",
        "percentage_type": "REMAINING",
    },

    # ========================================================
    # VOICE
    # ========================================================
    {
        "question": "How many voice minutes have I used?",
        "intent": "GET_VOICE_USAGE",
        "usage_type": None,
    },
    {
        "question": "How many calling minutes did I use in August?",
        "intent": "GET_VOICE_USAGE",
        "usage_type": None,
        "month": 8,
    },
    {
        "question": "How many call minutes do I have left?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "VOICE",
    },
    {
        "question": "What percentage of my voice allowance have I used?",
        "intent": "GET_USAGE_PERCENTAGE",
        "usage_type": "VOICE",
        "percentage_type": "CONSUMED",
    },

    # ========================================================
    # SMS
    # ========================================================
    {
        "question": "How many SMS have I sent?",
        "intent": "GET_USAGE_SUMMARY",
        "usage_type": None,
    },
    {
        "question": "How many text messages do I have left?",
        "intent": "GET_USAGE_REMAINING",
        "usage_type": "SMS",
    },
    {
        "question": "What percentage of my SMS allowance is remaining?",
        "intent": "GET_USAGE_PERCENTAGE",
        "usage_type": "SMS",
        "percentage_type": "REMAINING",
    },

    # ========================================================
    # SUMMARY
    # ========================================================
    {
        "question": "Give me my usage summary.",
        "intent": "GET_USAGE_SUMMARY",
        "usage_type": None,
    },
    {
        "question": "Show my current usage.",
        "intent": "GET_USAGE_SUMMARY",
        "usage_type": None,
    },
    {
        "question": "How am I doing on my allowances?",
        "intent": "GET_USAGE_SUMMARY",
        "usage_type": None,
    },
    {
        "question": "Show my data, voice and SMS usage.",
        "intent": "GET_USAGE_SUMMARY",
        "usage_type": None,
    },

    # ========================================================
    # HISTORICAL
    # ========================================================
    {
        "question": "How much data did I use last month?",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
        "time_range": "LAST_MONTH",
    },
    {
        "question": "How much data did I use in August?",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
        "month": 8,
    },
    {
        "question": "Show my July data usage.",
        "intent": "GET_DATA_USAGE",
        "usage_type": None,
        "month": 7,
    },
    {
        "question": "What was my voice usage last month?",
        "intent": "GET_VOICE_USAGE",
        "usage_type": None,
        "time_range": "LAST_MONTH",
    },

    # ========================================================
    # COMPARISON
    # ========================================================
    {
        "question": "Did I use more data this month than last month?",
        "intent": "GET_USAGE_COMPARISON",
        "usage_type": "DATA",
    },
    {
        "question": "Compare my data usage with last month.",
        "intent": "GET_USAGE_COMPARISON",
        "usage_type": "DATA",
    },
    {
        "question": "Compare August and September data usage.",
        "intent": "GET_USAGE_COMPARISON",
        "usage_type": "DATA",
        "month": 9,
        "comparison_month": 8,
    },
    {
        "question": "How much more data did I use in September than August?",
        "intent": "GET_USAGE_COMPARISON",
        "usage_type": "DATA",
        "month": 9,
        "comparison_month": 8,
    },

    # ========================================================
    # HISTORY
    # ========================================================
    {
        "question": "Show my data usage for the last 3 months.",
        "intent": "GET_USAGE_HISTORY",
        "usage_type": "DATA",
        "month_count": 3,
    },
    {
        "question": "Show my data usage for the last 6 months.",
        "intent": "GET_USAGE_HISTORY",
        "usage_type": "DATA",
        "month_count": 6,
    },
    {
        "question": "How much data have I used each month?",
        "intent": "GET_USAGE_HISTORY",
        "usage_type": "DATA",
    },

    # ========================================================
    # AVERAGE
    # ========================================================
    {
        "question": "What's my average monthly data usage?",
        "intent": "GET_USAGE_AVERAGE",
        "usage_type": "DATA",
    },
    {
        "question": "How much data do I normally use?",
        "intent": "GET_USAGE_AVERAGE",
        "usage_type": "DATA",
    },
    {
        "question": "What is my average data usage over the last 6 months?",
        "intent": "GET_USAGE_AVERAGE",
        "usage_type": "DATA",
        "month_count": 6,
    },

    # ========================================================
    # EXTREMES
    # ========================================================
    {
        "question": "Which month had my highest data usage?",
        "intent": "GET_USAGE_EXTREME",
        "usage_type": "DATA",
        "extreme_type": "HIGHEST",
    },
    {
        "question": "When did I use the most data?",
        "intent": "GET_USAGE_EXTREME",
        "usage_type": "DATA",
        "extreme_type": "HIGHEST",
    },
    {
        "question": "Which month had my lowest data usage?",
        "intent": "GET_USAGE_EXTREME",
        "usage_type": "DATA",
        "extreme_type": "LOWEST",
    },

    # ========================================================
    # TREND
    # ========================================================
    {
        "question": "Is my data usage increasing?",
        "intent": "GET_USAGE_TREND",
        "usage_type": "DATA",
    },
    {
        "question": "How has my data usage changed?",
        "intent": "GET_USAGE_TREND",
        "usage_type": "DATA",
    },
    {
        "question": "What's my internet usage trend?",
        "intent": "GET_USAGE_TREND",
        "usage_type": "DATA",
    },

    # ========================================================
    # AMBIGUOUS / UNSUPPORTED
    # ========================================================
    {
        "question": "How much is left?",
        "intent": "UNSUPPORTED",
        "usage_type": None,
    },
    {
        "question": "Predict how much data I'll use next month.",
        "intent": "UNSUPPORTED",
        "usage_type": None,
    },
    {
        "question": "Show me a chart of my future data usage.",
        "intent": "UNSUPPORTED",
        "usage_type": None,
    },
]