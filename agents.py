class Agent:
    def __init__(self, name, role, function, company=""):
        self.name: str = name
        self.role: str = role
        self.function: str = function
        self.company: str = company

    def set_company(self, company):
        self.company = company
        self.function = self.function.format(company=company)

    def __repr__(self) -> str:
        return f"Agent :{self.name} \nRole: {self.role} \nFunction: {self.function}"

    def __str__(self) -> str:
        return f"Agent :{self.name} \nRole: {self.role} \nFunction: {self.function}"

    def prompt(self, input_prompt):
        system_prompt = f"You are a: {self.name}. Your role: {self.role}. Your function: {self.function}. Based on your role and function, do the task you are given. Do not give me anything else other than the given task"

        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": input_prompt}]


news_classification_agent = Agent(
    name="New York News Classification Agent",  
    role="You are an agent that specializes in identifying news stories related to a specified company. Your role involves analyzing the provided news articles and answering specific questions about the company to determine if the article is relevant. Based on your analysis, provide a score reflecting the number of relevant indicators found.",
    function="""
    """
)


primary_analysis_agent = Agent(
    name="Primary Analysis Agent",
    role="You are a financial performance analysis agent specializing in assessing news articles to evaluate a company's financial health and potential impact on its stock price. Your role involves understanding the provided news articles and identifying key financial factors and market signals related to the company.",
    function="""Your function is to analyze the provided news stories about the company and identify recurring financial themes or noteworthy indicators that may influence its stock price or overall financial performance. 
    Based on these insights, create a list of specialized agents needed for deeper analysis. Provide a list of a MAXIMUM of 5 themed agents. Don't give more than 5.
    This includes assessing market sentiment, potential revenue or profit impacts, stock price fluctuations, competitive positioning, and regulatory or operational risks.
    Ensure the agent descriptions are clearly defined and relevant to financial analysis,
    with each description being clear, concise, and around 2 lines.

    Example:
    name:Stock Impact Agent
    description: Analyzes the news articles to identify factors that may positively or negatively affect the company's stock price, such as market sentiment, performance metrics, or external risks.
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
    name="Financial Impact Summary Agent",
    role="You are an expert financial analysis agent that extracts and summarizes key findings from the analysis report, focusing on the company's financial performance and potential impact on its stock price. Your role involves understanding the report and condensing the information into a concise summary that highlights the financial implications.",
    function="Your function is to read through the analysis report and provide a one-paragraph summary that captures the key financial insights. Focus on the potential impact on the company's financial performance, market position, and stock price. Ensure the summary is concise, clear, and relevant. Do not include anything unrelated to the financial impact or stock price implications."
)


published_date_agent = Agent(
    name="Published Date Agent",
    role="You are an expert in published date extraction from article html.",
    function="Your function is to extract the published date of the news article from the given html. Search for date patterns in the html. Extract it and convert it into ISO 8601 standard date format. If you can't find any dates provide 1970-01-01 as date."
)


search_terms_agent = Agent(
    name="Search Terms Agent",
    role="You are an agent specialized in creating optimized Google search queries to gather news articles focused on a company's financial performance. Your task is to craft queries that consider the company's business operations and industry context to extract the most relevant financial news, each paired with a tag describing its focus.",
    function="""Your function is to generate 5 targeted search term and tag pairs that will retrieve news articles related to the financial performance of {company}. 
    The search terms should reflect the company's core business activities, industry trends, market challenges, revenue drivers, strategic initiatives, and competitive positioning.
    Do not add any date information into the search terms!
    Each pair should consist of a concise search term and a corresponding tag that categorizes the focus of the search (e.g., "Earnings Analysis", "Market Sentiment", "Regulatory Impact", "Competitive Positioning", "Strategic Moves").
    Use the format: "search term": "tag". 
    Ensure each term is unique, directly relevant to {company}'s financial landscape, and do not provide more than 5 pairs.
    """
)


news_question_generator_agent = Agent(
    name="News Classification Question Generator Agent",
    role=(
        "You are an agent that specializes in generating tailored questions for classifying "
        "news stories related to a specified company. Your role involves analyzing the company's "
        "profile, industry context, and financial signals to create relevant questions that help "
        "determine if a news article pertains to the company."
    ),
    function="""
        For the company {company}, generate a set of up to 20 detailed yes/no questions designed to assess 
        the relevance of news articles. These questions should cover key areas such as financial 
        performance, product releases, technological advancements, market positioning, competitive 
        analysis, regulatory issues, operational updates, and strategic initiatives. Ensure each 
        question is specific to {company}'s context and phrased to elicit clear yes/no answers.
        Questions should not specify any dates

        In addition to the questions, provide a suggested threshold number representing the minimum 
        positive answers required for an article to be considered relevant to {company}. This threshold 
        should be based on the specificity and importance of the questions generated.

        Example output format:
        Questions:
        Q1-Does the article suggest any changes in {company}'s financial performance, such as revenue growth or earnings?
        Q2-Are there mentions of new products, services, or models by {company} that could impact its market?
        ...
        Threshold: X
    """
)
