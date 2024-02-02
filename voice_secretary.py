import streamlit as st
from openai import OpenAI
from audiorecorder import audiorecorder
import numpy as np
import os
from datetime import datetime
from gtts import gTTS
import base64

def ask_gpt(client, model, prompt):    
    response = client.chat.completions.create(model=model, messages=prompt)
    return response.choices[0].message.content
    

def STT(client, audio):
    filename = 'input.mp3'
    audio.export(out_f=filename)
    
    audio_file = open(filename,'rb')
    transcript = client.audio.transcriptions.create(model='whisper-1',file=audio_file)
    audio_file.close()    

    os.remove(filename)
    return transcript.text


def TTS(response):
    filename = 'response.mp3'
    tts = gTTS(text=response, lang='ko')
    tts.save(filename)

    with open(filename, 'rb') as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f'''
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            '''
        st.markdown(md, unsafe_allow_html=True,)
    os.remove(filename)


def main():

    client = None
    
    st.set_page_config(
        page_title='Voice_Secretary',
        layout='wide'
    )

    flag_start = False

    st.header('THFreeForAll.Voice_Secretary')
    st.markdown('---')
    
    with st.expander('THFreeForAll.Voice_Secretary',expanded=True):
        st.write(
            '''
            - UI : Streamlit
            - STT : OpenAI.Whisper
            - Answer : OpenAI.GPT.turbo.3.5
            - TTS : Google.TTS
            '''
        )
        st.markdown('---')

    with st.sidebar:        
        get_api_key = st.text_input(label='OPEN AI Key',placeholder='Enter your API Key',value='',type='password')        
        st.markdown('---')
        gpt_model_selected = st.radio(label='GPT Model',options=['gpt-3.5-turbo'])
        st.markdown('---')

        if st.button(label='Init'):
            st.session_state['chat'] = []
            st.session_state['message'] = [{'role':'system', 'content':'You are a thoughtful assistant. Respond to all input in 25 words and answer in korean'}]
            pass
    
    
    col1, col2 = st.columns(2)
    with col1:        
        st.subheader('Ask')
        
        if len(get_api_key) > 10:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", get_api_key))
            try:
                completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{'role':'user','content':'hello'}])
            except:
                client = None

        if client is not None:
            audio = audiorecorder(start_prompt="Start Recording", stop_prompt="Stop", pause_prompt="", key=None)
            if len(audio) > 0 and not np.array_equal(audio, st.session_state['check_audio']):
                st.audio(audio.export().read())
                question = STT(client, audio)
                now = datetime.now().strftime('%H:%M')
                st.session_state['chat'] = st.session_state['chat'] + [('user',now,question)]
                st.session_state['message'] = st.session_state['message'] + [{'role':'user','content':question}]
                st.session_state['check_audio'] = audio
                flag_start = True

    
    
    with col2:
        with st.container(height=300):
            st.subheader('Ask & Answer')
            if flag_start:            
                response = ask_gpt(client, gpt_model_selected, st.session_state['message'])
                st.session_state['message'] = st.session_state['message'] + [{'role':'system','content':response}]
                now = datetime.now().strftime('%H:%M')                
                
                st.session_state['chat'] = st.session_state['chat'] + [('bot', now, response)]

                for sender, time, message in st.session_state['chat']:
                    if sender == 'user':
                        with st.chat_message('user'):
                            st.write(message)
                    if sender == 'bot':
                        with st.chat_message('assistant'):
                            st.write(message)
                
                TTS(response)
                
                flag_start = False
    
    if 'chat' not in st.session_state:
        st.session_state['chat'] = []
    if 'message' not in st.session_state:
        st.session_state['message'] = [{'role':'system', 'content':'You are a thoughtful assistant. Respond to all input in 25 words and answer in korean'}]
    if 'check_audio' not in st.session_state:
        st.session_state['check_audio'] = []


if __name__ == '__main__':    
    main()
