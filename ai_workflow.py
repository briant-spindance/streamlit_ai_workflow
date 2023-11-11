from openai import OpenAI
import streamlit as st
import time

st.session_state["api_key"] = st.sidebar.text_input(
    "OpenAI API Key",
    type="password"
)

MODEL_CHOICES = {
    "gpt-3.5-turbo-1106": "GPT 3.5 Turbo",
    "gpt-4-1106-preview": "GPT 4 Turbo",
}

st.session_state["openai_model"] = st.sidebar.selectbox(
    "OpenAI Model",
    list(MODEL_CHOICES.keys()),
    format_func=lambda x: MODEL_CHOICES[x],
)

st.session_state["temperature"] = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.01,
)

client = OpenAI(
    api_key=st.session_state["api_key"],
)


st.title("Generative AI Workflow")
st.text(
    "This app demonstrates a workflow for generating text using a large language model"
)

seed = "The idea is: a chain of lemonade stands that sell lemonade and cookies."

templates = """
Identify the jobs to be done, desired gains, and pains to be relieved. Label it "Value Proposition"
---
Generate lean canvas from the original idea and Value Proposition. Label it "Lean Canvas"
---
Generate a detailed pro forma from the original Lean Canvas and Value Proposition.
Make assumptions as needed.
"""

print(st.session_state)

if "FormSubmitter:clear-Start Over" in st.session_state:
    del st.session_state["messages"]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle the initial form submission
chain_complete = False
with st.form("my_form"):
    templates = st.text_area("Enter Templates:", templates.strip(), height=300).split(
        "---"
    )
    text = st.text_area("Enter Initial Content:", seed, height=300)
    submitted = st.form_submit_button("Submit")
    if submitted:
        # Save the original message
        st.session_state.messages.append({"role": "user", "content": text})

        # Generate the content from the original sequence of templates
        message = templates[0] + "\n" + text
        st.session_state.messages.append({"role": "assistant", "content": message})
        for index, template in enumerate(templates):
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                ):
                    full_response += response.choices[0].delta.content or ""
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            if 0 <= index < len(templates) - 1:
                message = templates[index + 1] + "\n" + full_response
                st.session_state.messages.append(
                    {"role": "assistant", "content": message}
                )
        chain_complete = True

if chain_complete:
    st.success("Chain complete!")
    # Merge the messages into a single string
    content = "\n".join([m["content"] for m in st.session_state.messages])
    # File name is based on the truncated seed and the current timestamp
    file_name = f"{seed.replace(' ', '_')}_{int(time.time())}_output.md"

    st.download_button(
        "Download Output", content, file_name=file_name, mime="text/plain"
    )

    with st.form("clear"):
        clear_form_submited = st.form_submit_button("Start Over")
        if clear_form_submited:
            st.session_state["start_over"] = True
            chain_complete = False
