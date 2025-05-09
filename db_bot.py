import json
from openai import OpenAI
import os
import sqlite3
from time import time

fdir = os.path.dirname(__file__)
def getPath(fname):
    return os.path.join(fdir, fname)

# SQLITE
sqliteDbPath = getPath("aidb.sqlite")
setupSqlPath = getPath("setup.sql")
setupSqlDataPath = getPath("setupData.sql")

# Erase previous db
if os.path.exists(sqliteDbPath):
    os.remove(sqliteDbPath)

sqliteCon = sqlite3.connect(sqliteDbPath) # create new db
sqliteCursor = sqliteCon.cursor()
with (
        open(setupSqlPath) as setupSqlFile,
        open(setupSqlDataPath) as setupSqlDataFile
    ):

    setupSqlScript = setupSqlFile.read()
    setupSQlDataScript = setupSqlDataFile.read()

sqliteCursor.executescript(setupSqlScript) # setup tables and keys
sqliteCursor.executescript(setupSQlDataScript) # setup tables and keys

def runSql(query):
    result = sqliteCursor.execute(query).fetchall()
    return result

# OPENAI
configPath = getPath("config.json")
print(configPath)
with open(configPath) as configFile:
    config = json.load(configFile)

openAiClient = OpenAI(api_key = config["openaiKey"])

def getChatGptResponse(content):
    stream = openAiClient.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result


# strategies
commonSqlOnlyRequest = " Give me a sqlite select statement that returns the answer to the given question. Only respond with sqlite syntax. If there is an error do not explain it!"
strategies = {
    "zero_shot": setupSqlScript + commonSqlOnlyRequest,
    "single_domain_double_shot": (setupSqlScript +
                " Which New York Yankees player had the most career hits? " +
                "SELECT p.first_name, p.last_name, SUM(b.hits) AS total_hits\nFROM player p\nJOIN player_team pt ON p.id = pt.player_id\n" +
                "JOIN team t ON pt.team_id = t.id\nJOIN batting_stats b ON p.id = b.player_id AND t.year = b.year\nWHERE t.name = 'New York Yankees'\n" +
                "GROUP BY p.id\nORDER BY total_hits DESC\nLIMIT 1;"
                + commonSqlOnlyRequest)
}

questions = [
    #"Who has hit the most homeruns?",
    "Which pitcher has the most strikeouts?",
    "Which New York Yankees player had the most career hits?",
    "Which pitcher has to lowest ERA?",
    "Which pitcher has the best win to loss ratio?",
    #"Which players were on the 1928 New York Yankees?",
    #"Which players played in Left Field?",
    #"Which players bat lefty?",
    #"Which pitchers are southpaws?",
    #"Which players were born between 1960 and 1970?",
    #"Who has won the most MVP Awards?",
    #"What years did Randy Johnson win the Cy Young Award?",
    #"Did Nolan Ryan ever win a Cy Young?",
    "When did Shohei Ohtani move to the Los Angeles Dodgers?",
    "Which batter had the worst batting average in a season?",
    "Which non-pitcher had the worst batting average in a season?",
    "Who has had the most hits since 1970?"
]

def sanitizeForJustSql(value):
    gptStartSqlMarker = "```sql"
    gptEndSqlMarker = "```"
    if gptStartSqlMarker in value:
        value = value.split(gptStartSqlMarker)[1]
    if gptEndSqlMarker in value:
        value = value.split(gptEndSqlMarker)[0]

    if value.startswith("ite"):
        value = value[3:]
    return value

for strategy in strategies:
    responses = {"strategy": strategy, "prompt_prefix": strategies[strategy]}
    questionResults = []
    for question in questions:
        print(question)
        error = "None"
        try:
            getSqlFromQuestionEngineeredPrompt = strategies[strategy] + " " + question
            sqlSyntaxResponse = getChatGptResponse(getSqlFromQuestionEngineeredPrompt)
            sqlSyntaxResponse = sanitizeForJustSql(sqlSyntaxResponse)
            print(sqlSyntaxResponse)
            queryRawResponse = str(runSql(sqlSyntaxResponse))
            print(queryRawResponse)
            #oldFriendlyResultsPrompt = "I asked the question \"" + question +"\" and the response was \""+queryRawResponse+"\" Give a plain text response to the question  Please do not give any other suggests or chatter."
            friendlyResultsPrompt = "I asked the question: \"" + question +"\" and I queried this database: \n" + setupSqlScript + "\nwith this query \"" + sqlSyntaxResponse + "\". The query returned this result: \""+queryRawResponse+"\". Provide a simple plain text answer to my question using the information in the query and the result. Please do not give any other suggests or chatter."
            friendlyResponse = getChatGptResponse(friendlyResultsPrompt)
            print(friendlyResponse)
        except Exception as err:
            error = str(err)
            print(err)

        questionResults.append({
            "question": question,
            "sql": sqlSyntaxResponse,
            "queryRawResponse": queryRawResponse,
            "friendlyResponse": friendlyResponse,
            "error": error
        })

    responses["questionResults"] = questionResults

    with open(getPath(f"response_{strategy}_{time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent = 2)


sqliteCursor.close()
sqliteCon.close()
print("Done!")
