from src.tools import (
    get_stock_data,
    get_news,
    get_schema,
    execute_sql,
    save_memory,
    search_memory,
)


def register_all_tools(agent) -> None:
    agent.register_tool(get_stock_data.SCHEMA, get_stock_data.handler)
    agent.register_tool(get_news.SCHEMA, get_news.handler)
    agent.register_tool(get_schema.SCHEMA, get_schema.handler)
    agent.register_tool(execute_sql.SCHEMA, execute_sql.handler)
    agent.register_tool(save_memory.SCHEMA, save_memory.handler)
    agent.register_tool(search_memory.SCHEMA, search_memory.handler)
