import operator
import os
from typing import Annotated, List, Literal, TypedDict, Union
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, trim_messages
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize Model
# Using ChatOpenAI as MiniMax provides an OpenAI-compatible interface
llm = ChatOpenAI(
    model=os.getenv("MINIMAX_MODEL"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_API_BASE"), # Points to https://api.jiekou.ai/openai
    temperature=float(os.getenv("MINIMAX_TEMPERATURE", 0.7)),
    max_tokens=int(os.getenv("MINIMAX_MAX_TOKENS", 4096)),
)

# 1. Define State
# Using 'add_messages' reducer logic which is standard in LangGraph
class NakariState(TypedDict):
    # messages: The ephemeral conversation history for this turn (and potentially previous)
    messages: Annotated[List[BaseMessage], add_messages]
    # context_window: The actual subset of messages passed to the LLM (non-persistent, overwrite)
    context_window: List[BaseMessage]
    user_id: str
    response: str
    should_reflect: bool  # Signal from LLM to trigger background reflection

# 2. Node: Memory Retrieval
def retrieve_long_term_memory(state: NakariState):
    from context.manager import context_manager
    from utils.persona import persona_loader
    
    user_id = state["user_id"]
    
    # 1. Load Persona
    persona_name = context_manager.get_active_persona(user_id)
    persona_data = persona_loader.load_persona(persona_name)
    
    if persona_data:
        base_prompt = persona_loader.format_persona_prompt(persona_data)
        print(f"\n🎭 [Persona Loaded] Using template: '{persona_name}'")
    else:
        # Fallback
        base_prompt = (
            "You are Nakari, an AI with a distinct personality. "
            "You have memory and reflection capabilities.\n\n"
        )
    
    # 2. Retrieve Insights (Long Term Memory)
    insights = context_manager.get_insights(user_id, limit=5)
    
    # 3. Construct Meta Instructions
    meta_instruction = (
        "META-INSTRUCTION:\n"
        "If the user shares NEW, IMPORTANT information (e.g., name, preferences, life events, strong emotions) "
        "that you think should be permanently remembered or analyzed, you MUST start your response with the tag: [[REFLECT]].\n"
        "This tag is a hidden signal to your subsystem to trigger the memory consolidation process.\n"
        "Example:\n"
        "User: 'My name is Wenki.'\n"
        "Nakari: '[[REFLECT]] Nice to meet you, Wenki...'\n"
    )
    
    system_prompt_content = f"{base_prompt}\n{meta_instruction}"
    
    if insights:
        # Debug Print for CLI visualization
        print(f"🧠 [Internal Thought] Retrieved Insights from Hippocampus:")
        for idx, i in enumerate(insights):
            print(f"   {idx+1}. {i}")
        print(f"   ------------------------------------------------\n")
        
        insight_text = "\n".join([f"- {i}" for i in insights])
        system_prompt_content += f"\n\nInternal Reflection Insights (use these to personalize response):\n{insight_text}"
    else:
        print(f"🧠 [Internal Thought] No existing insights found in long-term memory.\n")
        system_prompt_content += "\n\nNo specific long-term insights yet."

    return {"messages": [SystemMessage(content=system_prompt_content)]}

# 3. Node: Context Window Management
def manage_context(state: NakariState):
    """
    Trims or compresses the context window before passing to LLM.
    Uses LangChain's trim_messages for precise token management.
    """
    messages = state["messages"]
    
    # Define token counter (approximate if no model, or use tiktoken/model.get_num_tokens)
    def simple_token_counter(msgs: List[BaseMessage]) -> int:
        # Simple approximation: 4 chars ~ 1 token
        text_content = "".join(m.content for m in msgs)
        return len(text_content) // 4

    # Trim Strategy:
    # 1. Keep max X tokens (e.g., 2000)
    # 2. Strategy "last": Keep most recent messages
    # 3. include_system=True: Always preserve the System Prompt (persona/instructions)
    # 4. start_on="human": Ensure the conversation history starts with a user message (after system)
    
    trimmed_messages = trim_messages(
        messages,
        max_tokens=2000,
        strategy="last",
        token_counter=simple_token_counter,
        include_system=True,
        allow_partial=False,
        start_on="human"
    )
    
    print(f"Context Manage: Creating context window with {len(trimmed_messages)} messages (from {len(messages)} total).")
    
    # We return 'context_window' which overwrites the field in NakariState
    # separate from the full 'messages' history
    return {"context_window": trimmed_messages}

# 4. Node: Generation
def generate_response(state: NakariState):
    # Use the curated context window, not the full history
    context = state.get("context_window", state["messages"])
    
    print(f"🤖 Generating with model: {os.getenv('MINIMAX_MODEL')}...")
    
    should_reflect = False
    generated_text = ""
    
    try:
        # Call actual LLM
        response_msg = llm.invoke(context)
        raw_text = response_msg.content
        
        # Check for Signal
        if "[[REFLECT]]" in raw_text:
            should_reflect = True
            print("✨ [Signal Detected] LLM requested reflection.")
            # Strip the tag from the final response
            generated_text = raw_text.replace("[[REFLECT]]", "").strip()
        else:
            generated_text = raw_text
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        generated_text = "I'm sorry, I'm having trouble connecting to my brain right now."

    return {
        "messages": [AIMessage(content=generated_text)],
        "response": generated_text,
        "should_reflect": should_reflect
    }

# Build the Graph
workflow = StateGraph(NakariState)

workflow.add_node("retrieve_memory", retrieve_long_term_memory)
workflow.add_node("manage_context", manage_context)
workflow.add_node("generate", generate_response)

workflow.add_edge(START, "retrieve_memory")
workflow.add_edge("retrieve_memory", "manage_context")
workflow.add_edge("manage_context", "generate")
workflow.add_edge("generate", END)

interaction_graph = workflow.compile()
