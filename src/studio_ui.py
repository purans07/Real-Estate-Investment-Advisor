"""Small presentation helpers. Architectural drawings are illustrative, not listing photos."""
from html import escape
import altair as alt
import streamlit as st

GREEN='#245749';GOLD='#b58857';INK='#242a27'

def architecture(kind='Apartment',large=False):
    villa=kind!='Apartment'
    if villa:
        shapes='<path d="M100 160 L225 65 L350 160" fill="#c3ac8a" stroke="#245749" stroke-width="2"/><path d="M125 160H325V280H125Z" fill="#f5f3ee" stroke="#245749" stroke-width="2"/><rect x="206" y="200" width="38" height="80" fill="#245749"/>'
        shapes+=''.join(f'<rect x="{x}" y="190" width="35" height="40" fill="#a9b9aa" stroke="#245749"/>' for x in [145,270])
    else:
        shapes='<path d="M130 95L265 55L335 95V280H130Z" fill="#f1ebde" stroke="#245749" stroke-width="2"/><path d="M265 55V280H335V95Z" fill="#b4c3b0" stroke="#245749" stroke-width="2"/>'
        shapes+=''.join(f'<path d="M{x} {y}h25v27h-25Z" fill="#6d8e79"/>' for x in [150,195,240] for y in [115,160,205])
        shapes+='<rect x="205" y="250" width="35" height="30" fill="#245749"/>'
    return '<svg viewBox="0 0 460 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Illustrative architectural drawing, not a property photograph"><circle cx="350" cy="65" r="38" fill="#d9c09a"/><path d="M30 280H430" stroke="#245749" stroke-width="2"/>'+shapes+'<path d="M65 280V210M65 245C15 230 30 180 65 190C105 180 115 225 65 245Z" fill="#a4b39a" stroke="#245749" stroke-width="2"/><path d="M370 280V230M370 255C345 245 350 220 370 220C390 220 400 245 370 255Z" fill="#a4b39a" stroke="#245749"/></svg>'

def eyebrow(text):st.markdown(f'<div class="eyebrow">{escape(text)}</div>',unsafe_allow_html=True)

def heading(title,subtitle=None):
    st.header(title)
    if subtitle:st.caption(subtitle)

def chart_style(chart):
    return chart.configure_view(strokeOpacity=0).configure_axis(gridColor='#e0e3da',domain=False,labelColor='#626c65',titleColor=INK,labelFontSize=11,titleFontSize=11).configure_legend(labelColor=INK,title=None).configure(background='transparent')

def bar_chart(frame,label,value,title=None):
    base=alt.Chart(frame).mark_bar(color=GREEN,cornerRadiusEnd=2).encode(x=alt.X(value+':Q',title=title or value),y=alt.Y(label+':N',sort='-x',title=None),tooltip=[label,alt.Tooltip(value+':Q',format=',.2f')]).properties(height=max(180,min(420,len(frame)*26)))
    st.altair_chart(chart_style(base),width='stretch')

def money(lakhs):
    return f'₹{lakhs/100:,.2f} Cr' if lakhs>=100 else f'₹{lakhs:,.2f} L'
