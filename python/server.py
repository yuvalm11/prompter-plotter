import os
import sys
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List
import uvicorn
import numpy as np
import cv2

from run_plotter import PlotterController
from utils import get_image, get_xys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = PlotterController()

@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Plotter Control</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 24px; }
      button { padding: 8px 12px; margin-right: 8px; }
      #log { white-space: pre-wrap; border: 1px solid #ccc; padding: 12px; min-height: 120px; }
      .row { margin-bottom: 12px; }
      input[type=text] { width: 320px; padding: 6px; }
    </style>
    <script src=\"/app.js?v=2\" defer></script>
  </head>
  <body>
    <h2>Plotter Control</h2>
    <div class=\"row\">
      <button id=\"btnStart\">Start</button>
      <button id=\"btnHome\">Home</button>
      <button id=\"btnOrigin\">Goto Origin</button>
      <button id=\"btnStop\">Stop</button>
      <button id=\"btnStatus\">Status</button>
    </div>
    <div class=\"row\">
      <input id=\"prompt\" type=\"text\" placeholder=\"Describe your drawing...\" />
      <button id=\"btnPrompt\">Load Prompt</button>
    </div>
    <div class=\"row\">
      <input id=\"file\" type=\"file\" accept=\"image/*\" />
      <button id=\"btnUpload\">Upload Image</button>
    </div>
    <div id=\"log\"></div>
  </body>
</html>
"""

@app.get("/app.js")
async def app_js() -> HTMLResponse:
    js = (
        """
// Minimal client-side script
window.api = async function(path, body) {
  const res = await fetch('/api/' + path, { method: 'POST', headers: {'Content-Type':'application/json'}, body: body?JSON.stringify(body):undefined });
  const data = await res.json().catch(()=>({}));
  window.log(path + ': ' + res.status + (data && data.message ? (' ' + data.message): ''));
  return data;
}
window.log = function(msg){
  const el = document.getElementById('log');
  if(el){ el.textContent += msg + '\\n'; }
}
window.sendPrompt = async function(){
  const promptEl = document.getElementById('prompt');
  const prompt = promptEl ? (promptEl.value || '') : '';
  const res = await fetch('/api/prompt', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({prompt}) });
  const data = await res.json();
  window.log('prompt queued paths: ' + (data && data.points ? data.points : 0));
}
window.uploadImage = async function(){
  const fileEl = document.getElementById('file');
  const file = fileEl && fileEl.files ? fileEl.files[0] : null;
  if(!file){ window.log('No file selected'); return; }
  const fd = new FormData(); fd.append('file', file);
  const res = await fetch('/api/image', { method:'POST', body: fd });
  const data = await res.json();
  window.log('image queued paths: ' + (data && data.points ? data.points : 0));
}
window.addEventListener('DOMContentLoaded', function(){
  const byId = (id)=>document.getElementById(id);
  const s = byId('btnStart'); if(s) s.addEventListener('click', ()=>window.api('start'));
  const h = byId('btnHome'); if(h) h.addEventListener('click', ()=>window.api('home'));
  const o = byId('btnOrigin'); if(o) o.addEventListener('click', ()=>window.api('goto_origin'));
  const st = byId('btnStop'); if(st) st.addEventListener('click', ()=>window.api('stop'));
  const status = byId('btnStatus'); if(status) status.addEventListener('click', async ()=>{
    const data = await window.api('status');
    window.log(JSON.stringify(data));
  });
  const p = byId('btnPrompt'); if(p) p.addEventListener('click', window.sendPrompt);
  const u = byId('btnUpload'); if(u) u.addEventListener('click', window.uploadImage);
});
"""
    )
    return HTMLResponse(js, media_type="application/javascript")

@app.post("/api/start")
async def api_start() -> Dict[str, Any]:
    await controller.start()
    return {"status": "ok"}

@app.post("/api/home")
async def api_home() -> Dict[str, Any]:
    await controller.home()
    return {"status": "ok"}

@app.post("/api/goto_origin")
async def api_goto_origin() -> Dict[str, Any]:
    await controller.goto_origin()
    return {"status": "ok"}

@app.post("/api/stop")
async def api_stop() -> Dict[str, Any]:
    await controller.shutdown()
    return {"status": "ok"}

@app.post("/api/status")
async def api_status() -> Dict[str, Any]:
    return {"started": controller.started}

@app.post("/api/prompt")
async def api_prompt(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = payload.get("prompt", "")
    img = get_image(prompt)
    xys = get_xys(img)
    await _queue_points(pts)
    return {"status": "ok"}#, "points": len(pts)}

@app.post("/api/image")
async def api_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    data = await file.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    xys = get_xys(img)
    pts = _scale_paths(xys)
    await _queue_points(pts)
    return {"status": "ok", "points": len(pts)}

async def _queue_points(points: List[List[float]]):
    if not controller.started:
        await controller.start()
    # Simple streaming of points to queue
    for xyz in points:
        await controller.machine.queue_planner.goto_via_queue(xyz, 100)
    await controller.flush()

def run():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    run()


