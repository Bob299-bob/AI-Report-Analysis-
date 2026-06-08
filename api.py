from fastapi import FastAPI
app=FastAPI(
    title='Multi Agent Research Agent'
)
from research import rag_system,retrieve,generate_report,search_net
@app.get('/')
def Home():
    return {'message':'Api Running'}
@app.post('/report')
def report(data:dict):
    try:
        input_data=data['input_data']
        query=data['query']
        index,chunks=rag_system(input_data)
        if len(chunks) == 0:
            return {"error": "No valid chunks"}
        context=retrieve(index,chunks,query)
        result=search_net(query)
        answer=generate_report(context,result,query)
        return answer
    except Exception as e:
        return {'error':str()}