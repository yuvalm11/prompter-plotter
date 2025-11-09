import os
import sys
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Tuple
import uvicorn
import numpy as np
import cv2
import matplotlib.pyplot as plt
import requests
import matplotlib.pyplot as plt

from run_plotter import PlotterController
from utils import get_image_url, get_xys, scale_paths

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = PlotterController(jog_rate=300)

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
      body { font-family: courier new; margin: 24px; font-size: large; background-color: #1a1a1a; color: #ffffff; }
      .container { max-width: 820px; width: 100%; margin: 0 auto;}
      .row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; width: 100%;}
      button { padding: 8px 12px; flex: 1; font-family: courier new; font-size: large; background-color: #333333; color: #ffffff; border: 1px solid #555555; max-width: 250px;}
      button:hover { background-color: #444444; }
      #log { white-space: pre-wrap; border: 1px solid #555555; padding: 12px; min-height: 120px; width: 100%; box-sizing: border-box; background-color: #2a2a2a; color: #ffffff; font-size: small; }
      input[type=text] { flex: 1; min-width: 0; padding: 8px 12px; font-family: courier new; background-color: #2a2a2a; color: #ffffff; border: 1px solid #555555; font-size: large; }
      input[type=file] { background-color: #2a2a2a; color: #ffffff; border: 1px solid #555555; padding: 9px 12px; flex: 1;}
    </style>
    <script src="/app.js?v=2" defer></script>
  </head>
  <body>
    <div class="container">
      <h2>Plotter Control</h2>
      <div class="row">
        <button id="btnStart" style="background-color: #006400;">Start</button>
        <button id="btnHome">Home</button>
        <button id="btnOrigin">Goto Origin</button>
        <button id="btnStop" style="background-color: #8B0000;">Stop</button>
        <button id="btnStatus">Status</button>
      </div>
      <div class="row">
        <input id="prompt" type="text" placeholder="Describe your drawing..." />
        <button id="btnPrompt">Load Prompt</button>
      </div>
      <div class="row">
        <input id="file" type="file" accept="image/*" />
        <button id="btnUpload">Upload Image</button>
      </div>
      <div id="log"></div>
    </div>
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
  window.log('received prompt: ' + prompt);
  const res = await fetch('/api/prompt', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({prompt}) });
  const data = await res.json();
  window.log('prompt queued paths: ' + (data && data.points ? data.points : 0));
  window.log('prompt image url: ' + (data && data.url ? data.url : ''));
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
    for(const key in data){
      window.log(key + ': ' + data[key]);
    }
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
    print("Received prompt: ", prompt)
    img_url = get_image_url(prompt, model="dall-e-3")
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
    xys = get_xys(img)
    extent = min(controller.machine_extents)
    pts = scale_paths(xys, extent)
    pts = [[(0, 0), (235, 0), (235, 235), (0, 235)]] + pts

    print(controller.machine.queue_planner._get_position_tail())
    
    await _queue_points(pts)
    return {"status": "ok", "points": len(pts), "url": img_url}

@app.post("/api/image")
async def api_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    data = await file.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    xys = get_xys(img)
    extent = min(controller.machine_extents)
    pts = scale_paths(xys, extent)
    pts = [[(0, 0), (235, 0), (235, 235), (0, 235)]] + pts
    # for contour in pts:
    #     for point in contour:
    #         plt.plot(point[0], point[1], 'r.')
    # plt.show()

    await _queue_points(pts)
    return {"status": "ok", "points": len(pts)}

async def _queue_points(points: List[List[Tuple[float, float]]]):
    # pen up
    await controller.goto_and_wait([0,0,0], controller.draw_rate)
    for contour in points:
        contour.append(contour[0])  # close the contour
        point = contour[0]
        await controller.goto_and_wait([point[0], point[1], 0], controller.draw_rate)
        await controller.goto_and_wait([point[0], point[1], 1], controller.draw_rate)
        for point in contour:
            x, y = point
            if 0 <= x <= 235 and 0 <= y <= 235:
                point = [point[0], point[1], 1]
                await controller.goto(point, controller.draw_rate)
            else:
                print(f"WARNING: Point ({x}, {y}) is outside trapezoid bounds")
                continue
        await controller.goto_and_wait([point[0], point[1], 0], controller.draw_rate)
    
    await controller.goto_origin()
    await controller.flush()


def run():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    run()
