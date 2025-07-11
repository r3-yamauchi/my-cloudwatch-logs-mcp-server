"""CloudWatch Logs Insights クエリ構文ドキュメント.

このモジュールは、CloudWatch Logs Insightsクエリ言語の包括的なドキュメントを提供します。
複数のAWS公式ドキュメントからの情報を統合し、LLMがインターネットアクセスなしで
クエリ構文を参照できるようにします。

データソース:
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Display.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Fields.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Filter.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-operations-functions.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Stats.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Parse.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Sort.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Pattern.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Limit.html
- https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Dedup.html
"""

from typing import Any, Dict, List


# CloudWatch Logs Insights クエリ構文の包括的なドキュメント
CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX: Dict[str, Any] = {
    "overview": {
        "title": "CloudWatch Logs Insights Language Query Syntax",
        "description": "CloudWatch Logs Insights supports a query language that provides powerful log analysis capabilities. The query syntax supports different functions and operations including general functions, arithmetic and comparison operations, and regular expressions.",
        "best_practices": [
            "Select only the necessary log groups for each query",
            "Always specify the narrowest possible time range for your queries",
            "Cancel all queries before closing the CloudWatch Logs Insights console page",
            "Ensure dashboard widgets are not refreshing at high frequency",
            "Use limit command to avoid consuming excessive tokens"
        ],
        "syntax_rules": [
            "Use pipe character (|) to separate multiple commands",
            "Use hash character (#) to add comments",
            "CloudWatch Logs automatically discovers fields starting with @ character",
            "All commands support Standard log class, Infrequent Access has some limitations"
        ]
    },
    "commands": {
        "display": {
            "description": "Displays a specific field or fields in query results",
            "syntax": "display field1, field2, ...",
            "behavior": "Shows only the fields you specify. If multiple display commands are used, only the final one takes effect.",
            "examples": [
                {
                    "title": "Display one field",
                    "query": "fields @message\\n| parse @message \"[*] *\" as loggingType, loggingMessage\\n| filter loggingType = \"ERROR\"\\n| display loggingMessage",
                    "explanation": "Extracts logging type and message, filters for ERROR logs, and displays only the message"
                }
            ],
            "tips": [
                "Use display only once in a query for best results",
                "If used multiple times, only the last display command takes effect"
            ]
        },
        "fields": {
            "description": "Shows specific fields in query results with support for functions and operations",
            "syntax": "fields field1, field2, expression as alias",
            "behavior": "If multiple fields commands are used without display, all specified fields are shown",
            "examples": [
                {
                    "title": "Display specific fields",
                    "query": "fields @timestamp, @message\\n| sort @timestamp desc\\n| limit 20",
                    "explanation": "Shows timestamp and message fields, sorted by timestamp in descending order, limited to 20 results"
                },
                {
                    "title": "Create extracted fields",
                    "query": "fields ispresent(@message) as hasMessage, @timestamp",
                    "explanation": "Creates a new field 'hasMessage' based on whether @message field exists"
                }
            ],
            "tips": [
                "Use fields instead of display when you need to use functions",
                "Support for creating new fields with 'as' keyword"
            ]
        },
        "filter": {
            "description": "Filters log events that match one or more conditions",
            "syntax": "filter condition",
            "operators": {
                "comparison": ["=", "!=", "<", "<=", ">", ">="],
                "boolean": ["and", "or", "not"],
                "pattern_matching": ["like", "not like", "=~", "in", "not in"]
            },
            "examples": [
                {
                    "title": "Single condition filter",
                    "query": "fields @timestamp, @message\\n| filter range > 3000\\n| sort @timestamp desc\\n| limit 20",
                    "explanation": "Filters events where range field is greater than 3000"
                },
                {
                    "title": "Multiple conditions",
                    "query": "filter range > 3000 and accountId = 123456789012",
                    "explanation": "Filters events matching both conditions using AND operator"
                },
                {
                    "title": "Pattern matching with like",
                    "query": "filter @message like \"Exception\"",
                    "explanation": "Filters events where @message contains 'Exception'"
                },
                {
                    "title": "Regular expression",
                    "query": "filter @message =~ /Exception/",
                    "explanation": "Filters events using regular expression pattern"
                },
                {
                    "title": "Case-insensitive matching",
                    "query": "filter @message like /(?i)Exception/",
                    "explanation": "Filters events with case-insensitive pattern matching"
                },
                {
                    "title": "Set membership",
                    "query": "filter logGroup in [\"example_group\"]",
                    "explanation": "Filters events where logGroup field matches one of the specified values"
                }
            ],
            "indexed_fields": {
                "description": "Field indexes can improve query performance for specific filter patterns",
                "supported_patterns": ["filter fieldName = value", "filter fieldName IN [values]"],
                "not_supported": ["filter fieldName like pattern"],
                "example": {
                    "query": "filter requestId = \"1234656\"",
                    "explanation": "Uses field index on requestId if available to improve performance"
                }
            }
        },
        "stats": {
            "description": "Calculate aggregate statistics and create visualizations",
            "syntax": "stats function(field) by grouping_field",
            "aggregation_functions": {
                "avg": "Average of numeric values",
                "count": "Count of events or non-null values",
                "count_distinct": "Count of unique values",
                "max": "Maximum value",
                "min": "Minimum value",
                "pct": "Percentile calculation",
                "stddev": "Standard deviation",
                "sum": "Sum of numeric values"
            },
            "non_aggregation_functions": {
                "earliest": "Value from earliest timestamp",
                "latest": "Value from latest timestamp",
                "sortsFirst": "First value in sort order",
                "sortsLast": "Last value in sort order"
            },
            "examples": [
                {
                    "title": "Time series visualization",
                    "query": "stats count(*) by queryType, bin(1h)",
                    "explanation": "Creates visualization showing distribution of query types per hour"
                },
                {
                    "title": "Average calculation",
                    "query": "stats avg(myfield1) by bin(5m)",
                    "explanation": "Calculates average values with 5-minute time buckets"
                },
                {
                    "title": "Multiple aggregations",
                    "query": "stats avg(bytes), max(bytes) by dstAddr",
                    "explanation": "Calculates both average and maximum bytes per destination address"
                },
                {
                    "title": "Grouped statistics",
                    "query": "stats count(*) by queryType",
                    "explanation": "Counts events grouped by query type"
                }
            ],
            "multiple_stats": {
                "description": "Up to two stats commands can be used in a single query",
                "limitations": [
                    "Maximum of two stats commands per query",
                    "sort/limit must appear after second stats command",
                    "Second stats can only reference fields from first stats",
                    "bin function requires @timestamp field propagation"
                ],
                "example": {
                    "query": "FIELDS strlen(@message) AS message_length\\n| STATS sum(message_length)/1024/1024 as logs_mb BY bin(5m)\\n| STATS max(logs_mb) AS peak_ingest_mb, min(logs_mb) AS min_ingest_mb",
                    "explanation": "First stats aggregates by time, second stats finds peak and minimum values"
                }
            }
        },
        "parse": {
            "description": "Extracts data from log fields using glob patterns or regular expressions",
            "syntax": "parse field \"pattern\" as field1, field2",
            "modes": {
                "glob": "Use wildcards (*) for pattern matching",
                "regex": "Use regular expressions for complex patterns"
            },
            "examples": [
                {
                    "title": "Glob pattern extraction",
                    "query": "parse @message \"user=*, method:*, latency := *\" as @user, @method, @latency",
                    "explanation": "Extracts user, method, and latency using glob patterns"
                },
                {
                    "title": "Regular expression extraction",
                    "query": "parse @message /user=(?<user2>.*?), method:(?<method2>.*?), latency := (?<latency2>.*?)/",
                    "explanation": "Extracts fields using named capturing groups in regex"
                },
                {
                    "title": "Named capturing groups",
                    "query": "parse @message /(?<NetworkInterface>eni-.*?) / | display NetworkInterface",
                    "explanation": "Extracts network interface ID using named capture group"
                },
                {
                    "title": "Complex parsing with filtering",
                    "query": "FIELDS @message\\n| PARSE @message \"* [*] *\" as loggingTime, loggingType, loggingMessage\\n| FILTER loggingType IN [\"ERROR\", \"INFO\"]\\n| DISPLAY loggingMessage, loggingType = \"ERROR\" as isError",
                    "explanation": "Parses log format, filters by type, and creates boolean field"
                }
            ],
            "limitations": [
                "JSON events are flattened during ingestion",
                "Nested JSON parsing requires regex, not glob",
                "Maximum 200 fields per JSON event"
            ]
        },
        "sort": {
            "description": "Displays log events in ascending (asc) or descending (desc) order",
            "syntax": "sort field [asc|desc]",
            "algorithm": "Updated natural sorting algorithm",
            "sorting_rules": [
                "Non-number values come before number values",
                "Numeric portions ordered by length then numerical value",
                "Non-numeric portions ordered by Unicode values"
            ],
            "examples": [
                {
                    "title": "Descending timestamp sort",
                    "query": "sort @timestamp desc",
                    "explanation": "Sorts events by timestamp in descending order"
                },
                {
                    "title": "Top N query",
                    "query": "stats sum(packets) as packetsTransferred by srcAddr, dstAddr\\n| sort packetsTransferred desc\\n| limit 15",
                    "explanation": "Finds top 15 packet transfers between hosts"
                }
            ]
        },
        "pattern": {
            "description": "Automatically clusters log data into patterns",
            "syntax": "pattern field",
            "input_types": ["@message field", "extracted field from parse", "string manipulated field"],
            "output_fields": {
                "@pattern": "Shared text structure with dynamic tokens",
                "@ratio": "Ratio of log events matching the pattern",
                "@sampleCount": "Count of events matching the pattern",
                "@severityLabel": "Log severity level (Error, Warning, Info, Debug)"
            },
            "examples": [
                {
                    "title": "Basic pattern analysis",
                    "query": "pattern @message",
                    "explanation": "Identifies common patterns in log messages"
                },
                {
                    "title": "Pattern with filtering",
                    "query": "filter @message like /ERROR/\\n| pattern @message",
                    "explanation": "Finds patterns only in error messages"
                },
                {
                    "title": "Pattern with parsing",
                    "query": "filter @message like /ERROR/\\n| parse @message 'Failed to do: *' as cause\\n| pattern cause\\n| sort @sampleCount asc",
                    "explanation": "Extracts error causes, finds patterns, and sorts by frequency"
                }
            ],
            "token_types": [
                "Error codes, IP addresses, timestamps, request IDs",
                "Dynamic tokens represented as <Type-Number> or <Token-Number>"
            ]
        },
        "limit": {
            "description": "Specifies maximum number of log events to return",
            "syntax": "limit number",
            "default": "10,000 log events if omitted",
            "examples": [
                {
                    "title": "Limit recent events",
                    "query": "fields @timestamp, @message\\n| sort @timestamp desc\\n| limit 25",
                    "explanation": "Returns only the 25 most recent log events"
                }
            ]
        },
        "dedup": {
            "description": "Removes duplicate results based on field values",
            "syntax": "dedup field1, field2, ...",
            "behavior": [
                "Keeps first result in sort order",
                "Null values are not considered duplicates",
                "Use with sort for predictable results"
            ],
            "examples": [
                {
                    "title": "Deduplicate by server",
                    "query": "fields @timestamp, server, severity, message\\n| sort @timestamp desc\\n| dedup server",
                    "explanation": "Shows most recent event for each unique server"
                }
            ],
            "limitations": [
                "Only limit command can follow dedup",
                "Use filter with isPresent() to eliminate null values"
            ]
        },
        "diff": {
            "description": "Compares log events with previous time period to identify trends",
            "syntax": "diff",
            "behavior": "Compares current time period with previous period of equal length",
            "use_cases": ["Trend analysis", "New log event detection"],
            "limitations": ["Not supported in Infrequent Access log class"]
        },
        "unmask": {
            "description": "Displays masked content from data protection policies",
            "syntax": "unmask",
            "use_case": "Shows full content of logs with data protection masking",
            "limitations": ["Not supported in Infrequent Access log class"]
        },
        "unnest": {
            "description": "Flattens lists into multiple records",
            "syntax": "unnest field",
            "behavior": "Produces multiple records with single record per list element"
        },
        "filterIndex": {
            "description": "Forces query to use field indexes for performance",
            "syntax": "filterIndex field",
            "behavior": "Attempts to scan only indexed log groups",
            "limitations": ["Not supported in Infrequent Access log class"]
        },
        "SOURCE": {
            "description": "Specifies log groups by prefix, account, and class",
            "syntax": "SOURCE '/log-group-prefix' [account:123456789012] [class:STANDARD]",
            "limitations": ["Supported only in CLI/API, not console"],
            "use_case": "Specify large number of log groups efficiently"
        }
    },
    "functions": {
        "arithmetic": {
            "description": "Arithmetic operators for numeric calculations",
            "operators": {
                "+": "Addition",
                "-": "Subtraction",
                "*": "Multiplication",
                "/": "Division",
                "^": "Exponentiation (2^3 = 8)",
                "%": "Remainder/modulus (10%3 = 1)"
            },
            "examples": [
                {
                    "expression": "field1 + field2",
                    "description": "Adds two numeric fields"
                },
                {
                    "expression": "bytes / 1024",
                    "description": "Converts bytes to kilobytes"
                }
            ]
        },
        "boolean": {
            "description": "Boolean operators for logical operations",
            "operators": {
                "and": "Logical AND",
                "or": "Logical OR",
                "not": "Logical NOT"
            },
            "usage": "Only in functions returning TRUE/FALSE"
        },
        "comparison": {
            "description": "Comparison operators for all data types",
            "operators": {
                "=": "Equal",
                "!=": "Not equal",
                "<": "Less than",
                ">": "Greater than",
                "<=": "Less than or equal",
                ">=": "Greater than or equal"
            },
            "return_type": "Boolean"
        },
        "numeric": {
            "description": "Numeric functions for mathematical operations",
            "functions": {
                "abs(a)": "Absolute value",
                "ceil(a)": "Round to ceiling",
                "floor(a)": "Round to floor",
                "greatest(a, b, ...)": "Largest value",
                "least(a, b, ...)": "Smallest value",
                "log(a)": "Natural logarithm",
                "sqrt(a)": "Square root"
            },
            "examples": [
                {
                    "expression": "abs(-5)",
                    "result": "5"
                },
                {
                    "expression": "ceil(3.14)",
                    "result": "4"
                }
            ]
        },
        "datetime": {
            "description": "Date and time functions for temporal operations",
            "time_units": {
                "ms": "milliseconds (cap: 1000)",
                "s": "seconds (cap: 60)",
                "m": "minutes (cap: 60)",
                "h": "hours (cap: 24)",
                "d": "days",
                "w": "weeks",
                "mo": "months",
                "q": "quarters",
                "y": "years"
            },
            "functions": {
                "bin(period)": "Rounds @timestamp to time period",
                "datefloor(timestamp, period)": "Truncates timestamp to period",
                "dateceil(timestamp, period)": "Rounds up timestamp to period",
                "fromMillis(number)": "Converts milliseconds to timestamp",
                "toMillis(timestamp)": "Converts timestamp to milliseconds",
                "now()": "Returns current epoch seconds"
            },
            "examples": [
                {
                    "expression": "bin(5m)",
                    "description": "Creates 5-minute time buckets"
                },
                {
                    "expression": "toMillis(@timestamp)",
                    "description": "Converts timestamp to milliseconds since epoch"
                },
                {
                    "query": "filter toMillis(@timestamp) >= (now() * 1000 - 7200000)",
                    "description": "Filters events from past 2 hours"
                }
            ]
        },
        "string": {
            "description": "String manipulation functions",
            "functions": {
                "isempty(str)": "Returns 1 if field is missing or empty",
                "isblank(str)": "Returns 1 if field is missing, empty, or whitespace",
                "concat(str1, str2, ...)": "Concatenates strings",
                "ltrim(str, [chars])": "Removes characters from left",
                "rtrim(str, [chars])": "Removes characters from right",
                "trim(str, [chars])": "Removes characters from both ends",
                "strlen(str)": "Returns string length in Unicode points",
                "toupper(str)": "Converts to uppercase",
                "tolower(str)": "Converts to lowercase",
                "substr(str, start, [length])": "Returns substring",
                "replace(str, search, replace)": "Replaces all instances",
                "strcontains(str, search)": "Returns 1 if contains substring"
            },
            "examples": [
                {
                    "expression": "toupper(@message)",
                    "description": "Converts message to uppercase"
                },
                {
                    "expression": "substr(@message, 0, 10)",
                    "description": "Gets first 10 characters"
                },
                {
                    "expression": "replace(@message, \"ERROR\", \"WARN\")",
                    "description": "Replaces all ERROR with WARN"
                }
            ]
        },
        "json": {
            "description": "JSON parsing and manipulation functions",
            "functions": {
                "jsonParse(str)": "Parses JSON string to map/list",
                "jsonStringify(obj)": "Converts map/list to JSON string"
            },
            "examples": [
                {
                    "expression": "jsonParse(@message) as json_msg",
                    "description": "Parses JSON message into object"
                },
                {
                    "query": "fields jsonParse(@message) as json_message\\n| stats count() by json_message.status_code",
                    "description": "Groups by JSON field value"
                }
            ],
            "structure_access": {
                "map": "Use dot notation: obj.field or obj.`special.field`",
                "list": "Use bracket notation: list[index]"
            }
        },
        "ip_address": {
            "description": "IP address validation and subnet checking",
            "functions": {
                "isValidIp(str)": "Validates IPv4 or IPv6 address",
                "isValidIpV4(str)": "Validates IPv4 address",
                "isValidIpV6(str)": "Validates IPv6 address",
                "isIpInSubnet(ip, subnet)": "Checks if IP is in CIDR subnet",
                "isIpv4InSubnet(ip, subnet)": "Checks if IPv4 is in subnet",
                "isIpv6InSubnet(ip, subnet)": "Checks if IPv6 is in subnet"
            },
            "examples": [
                {
                    "expression": "isValidIp(clientIp)",
                    "description": "Validates client IP address"
                },
                {
                    "expression": "isIpInSubnet(clientIp, \"192.168.1.0/24\")",
                    "description": "Checks if IP is in private subnet"
                }
            ]
        },
        "general": {
            "description": "General utility functions",
            "functions": {
                "ispresent(field)": "Returns true if field exists",
                "coalesce(field1, field2, ...)": "Returns first non-null value"
            },
            "examples": [
                {
                    "expression": "ispresent(@requestId)",
                    "description": "Checks if request ID field exists"
                },
                {
                    "expression": "coalesce(@clientIp, @sourceIp, \"unknown\")",
                    "description": "Returns first available IP field or default"
                }
            ]
        }
    },
    "examples": {
        "common_patterns": [
            {
                "title": "Find exceptions per hour",
                "query": "filter @message like /Exception/\\n| stats count(*) as exceptionCount by bin(1h)\\n| sort exceptionCount desc",
                "use_case": "Error monitoring and trend analysis"
            },
            {
                "title": "Top error patterns",
                "query": "filter @message like /ERROR/\\n| pattern @message\\n| sort @sampleCount desc\\n| limit 10",
                "use_case": "Identify most common error patterns"
            },
            {
                "title": "Slow requests analysis",
                "query": "filter @duration > 1000\\n| stats avg(@duration), max(@duration), count() by bin(5m)\\n| sort @timestamp desc",
                "use_case": "Performance monitoring"
            },
            {
                "title": "User activity by hour",
                "query": "parse @message \"user=* action=*\" as user, action\\n| stats count() by user, bin(1h)\\n| sort @timestamp desc",
                "use_case": "User behavior analysis"
            },
            {
                "title": "Network traffic analysis",
                "query": "stats sum(bytes) as totalBytes by srcAddr, dstAddr\\n| sort totalBytes desc\\n| limit 20",
                "use_case": "Network monitoring"
            }
        ],
        "advanced_queries": [
            {
                "title": "Multi-step aggregation",
                "query": "FIELDS strlen(@message) AS message_length\\n| STATS sum(message_length)/1024/1024 as logs_mb BY bin(5m)\\n| STATS max(logs_mb) AS peak_mb, avg(logs_mb) AS avg_mb",
                "use_case": "Log volume analysis with multiple aggregation levels"
            },
            {
                "title": "Complex filtering with JSON",
                "query": "fields jsonParse(@message) as json_msg\\n| filter json_msg.status_code >= 400\\n| stats count() by json_msg.endpoint, bin(10m)",
                "use_case": "API error rate monitoring"
            },
            {
                "title": "IP subnet analysis",
                "query": "filter isIpInSubnet(@clientIp, \"10.0.0.0/8\")\\n| stats count() as internal_requests by bin(1h)\\n| sort @timestamp desc",
                "use_case": "Internal vs external traffic analysis"
            }
        ]
    },
    "troubleshooting": {
        "common_issues": [
            {
                "issue": "Query timeout",
                "solutions": [
                    "Reduce time range",
                    "Add more specific filters",
                    "Use limit command",
                    "Optimize field selection"
                ]
            },
            {
                "issue": "High costs",
                "solutions": [
                    "Use narrower time ranges",
                    "Filter early in query",
                    "Select fewer log groups",
                    "Use field indexes when available"
                ]
            },
            {
                "issue": "Empty results",
                "solutions": [
                    "Check field names (case sensitive)",
                    "Verify filter conditions",
                    "Confirm time range",
                    "Use ispresent() to check field existence"
                ]
            }
        ]
    }
}

def get_query_syntax_documentation() -> Dict[str, Any]:
    """CloudWatch Logs Insights クエリ構文の完全なドキュメントを取得する.

    Returns:
        Dict[str, Any]: クエリ構文の包括的なドキュメント
    """
    return CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX

def get_command_documentation(command: str) -> Dict[str, Any]:
    """特定のコマンドのドキュメントを取得する.

    Args:
        command: コマンド名 (例: 'filter', 'stats', 'parse')

    Returns:
        Dict[str, Any]: 指定されたコマンドのドキュメント

    Raises:
        KeyError: 指定されたコマンドが存在しない場合
    """
    if command not in CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["commands"]:
        raise KeyError(f"Command '{command}' not found in documentation")

    return CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["commands"][command]

def get_function_documentation(function_category: str) -> Dict[str, Any]:
    """特定の関数カテゴリのドキュメントを取得する.

    Args:
        function_category: 関数カテゴリ (例: 'string', 'datetime', 'numeric')

    Returns:
        Dict[str, Any]: 指定された関数カテゴリのドキュメント

    Raises:
        KeyError: 指定された関数カテゴリが存在しない場合
    """
    if function_category not in CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["functions"]:
        raise KeyError(f"Function category '{function_category}' not found in documentation")

    return CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["functions"][function_category]

def search_documentation(search_term: str) -> List[Dict[str, Any]]:
    """ドキュメント内でキーワード検索を行う.

    Args:
        search_term: 検索キーワード

    Returns:
        List[Dict[str, Any]]: 検索結果のリスト
    """
    results = []
    search_term_lower = search_term.lower()

    # コマンドから検索
    for command_name, command_doc in CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["commands"].items():
        if (search_term_lower in command_name.lower() or
            search_term_lower in command_doc.get("description", "").lower()):
            results.append({
                "type": "command",
                "name": command_name,
                "documentation": command_doc
            })

    # 関数から検索
    for func_category, func_doc in CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["functions"].items():
        if (search_term_lower in func_category.lower() or
            search_term_lower in func_doc.get("description", "").lower()):
            results.append({
                "type": "function_category",
                "name": func_category,
                "documentation": func_doc
            })

    return results

def get_available_commands() -> List[str]:
    """利用可能なコマンドのリストを取得する.

    Returns:
        List[str]: コマンド名のリスト
    """
    return list(CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["commands"].keys())

def get_available_function_categories() -> List[str]:
    """利用可能な関数カテゴリのリストを取得する.

    Returns:
        List[str]: 関数カテゴリ名のリスト
    """
    return list(CLOUDWATCH_LOGS_INSIGHTS_QUERY_SYNTAX["functions"].keys())
