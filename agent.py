class Agent:
    def __init__(self, name, role, function):
        self.name: str = name
        self.role: str = role
        self.function: str = function

    def __repr__(self) -> str:
        return f"Agent :{self.name} \nRole: {self.role} \nFunction: {self.function}"

    def __str__(self) -> str:
        return f"Agent :{self.name} \nRole: {self.role} \nFunction: {self.function}"

    def prompt(self, input_prompt):
        system_prompt = f"You are a: {self.name}. Your role: {self.role}. Your function: {self.function}. Based on your role and function, do the task you are given. Do not give me anything else other than the given task"

        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": input_prompt}]


news_classification_agent = Agent(
    name="New York News Classification Agent",
    role="You are an agent that specializes in identifying news stories related to New York. Your role involves analyzing the provided news articles and answer 5 yes/no questions in order to decide if the article is related to New York or not. Answer the questions and provide the number of yes answers as score.",
    function="""Q1-Does the article explicitly mention New York State or the New York region in the context of energy?
        Q2-Does the article discuss energy prices, supply, or demand specifically within New York?
        Q3-Does the article address policies, regulations, or legislative actions that affect the New York energy market?
        Q4-Does the article highlight significant projects, technological advancements, or infrastructure developments within New York's energy sector?
        Q5-Are key organizations, companies, or public figures involved in New York's energy market mentioned in the article?
        Q6-Is this article relevant to a utility-scale renewable energy or battery energy storage project developer in the New York region?
        Q7-Does this article provide new and crucial information about aspects such as interconnection queue regulations, transmission grid planning, state incentives, or capacity market requirements that impact the development, origination, and project finance of renewable and battery energy storage projects in New York?
        Q8-Does this article offer up-to-date news and announcements that would assist a renewable or battery energy storage project developer in making critical financial investment decisions in the New York region?
        Q9-Does this article provide insights into the operations, development, or retirement of renewable energy power plants (including onshore/offshore wind farms, solar power plants, co-located energy storage facilities, hydrogen plants, hydropower stations, or nuclear plants) within the New York region?
        Q10-Does this article report on new technological advancements or breakthroughs that impact the energy industry's operation, evolution, or development in North America, with relevance to the New York energy sector?
""",
)

primary_analysis_agent = Agent(
    name="Primary Analysis Agent",
    role="You are a renewable energy specialist agent that analyzes the fetched news stories related to renewable energy market to identify key financial themes and topics. Your role involves understanding the overall context and pinpointing significant elements within the news data about the renewable energy market",
    function="""Your function is to analyze the provided news stories about renewable energy 
    and identify recurring financial themes or noteworthy topics. 
    Based on these themes, create a list of specialized agents needed for deeper analysis specific to the market. Provide a list of a MAXIMUM of 5 themed agents. Don't give more than 5.
    This includes identifying relevant sectors, potential market impacts, historical financial trends, 
    expert financial opinions, and other pertinent market changing factors. 
    Ensure the agent descriptions are clearly defined and relevant to the market news,
    with each description being clear, concise, and around 2 lines.

    Example:
    name:Industry Trends Agent description: Analyzes industry trends and developments in the renewable energy sector to identify new opportunities and detect potential impacts on the industry.
    """,
)

agent_creator_agent = Agent(
    name="Agent creating agent",
    role="You are an helpful agent that generates the formatted reply for a given task. Your role is to give back the name of a agent that can do the given prompt task, the role of that child agent that would perfectly describe for it to do the given task and the function that the child agent will perform for it to do the given task. you will write the role and function in second person to describe the agent as this will be used to create and inform the agent of its role and function",
    function="""Your function is to create a child agent that will perform the given task in prompt, think carefully and given the description, pass on the name, role and function of this agent please. The role and function needs to be descriptive with two to three sentences describing them in detail. Make sure the role and function are relevant to the task in the prompt and multiline sentences but short and concise.

    Example :
    name : Search Term Generation Agent
    role : You are an agent that examines the given market news and a list of analyzing agents, focusing on identifying the necessary search terms. Your role involves understanding the key themes and specific analysis needs to provide targeted search terms for gathering relevant articles related to renewable energy market.
    function: Your function is to read through the provided news stories about renewable energy and the list of analyzing agents with their specific roles. Based on this information, you generate a list of search terms that will help fetch relevant articles from various sources for further analysis by the specialized agents. The search terms should be tailored to address the key themes, potential impacts, and specific financial aspects mentioned in the news that are relevant to the agents to understand various aspects. Do not just give generic terms, give more tuned terms that combines the renewable energy market news with the agent's purpose for agents to benifit from these search terms.
    """,
)

summary_agent = Agent(
    name="Renewable Energy Report Summary Agent",
    role="You are an expert analyst agent that extracts and summarizes only the key findings from the analysis report. Your role involves understanding the report and condensing the information into a concise summary that captures the essence of the article.",
    function="Your function is to read through the analysis report and give one paragraph of summary. Write the summary concisely, ensuring that it captures the essence of article. Make it short and concise. Do not give anthying else other than the summary.",
)

published_date_agent = Agent(
    name="Published Date Agent",
    role="You are an expert in published date extraction from article html.",
    function="Your function is to extract the published date of the news article from the given html. Search for date patterns in the html. Extract it and convert it into ISO 8601 standard date format. If you can't find any dates provide 1970-01-01 as date."
)
