/**
 * ComfyUI Resolution Presets Web Extension
 * 提供更好的UI体验和预览功能
 */

import { app } from "../../scripts/app.js";

// 扩展ResolutionPresetImage节点，添加预览功能
app.registerExtension({
    name: "ComfyUI.ResolutionPresets.WebExtension",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ResolutionPresetImage") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this) : undefined;
                
                // 添加预览按钮
                if (this.widgets) {
                    this.addWidget("button", "预览尺寸", null, () => {
                        this.showPreview();
                    });
                }
                
                return r;
            };
            
            // 添加预览方法
            nodeType.prototype.showPreview = function() {
                const width = this.widgets.find(w => w.name === "宽度")?.value || 512;
                const height = this.widgets.find(w => w.name === "高度")?.value || 512;
                
                const previewWindow = window.open('', '_blank');
                previewWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>分辨率预览 - ${width}×${height}</title>
                        <style>
                            body { 
                                margin: 0; 
                                padding: 20px; 
                                font-family: Arial, sans-serif; 
                                background: #f0f0f0; 
                            }
                            .container { 
                                max-width: 800px; 
                                margin: 0 auto; 
                                background: white; 
                                padding: 20px; 
                                border-radius: 10px; 
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                            }
                            .preview-area { 
                                width: 100%; 
                                height: 400px; 
                                border: 2px dashed #ccc; 
                                margin: 20px 0; 
                                display: flex; 
                                align-items: center; 
                                justify-content: center; 
                                position: relative; 
                                background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%, transparent 75%, #f0f0f0 75%, #f0f0f0),
                                            linear-gradient(45deg, #f0f0f0 25%, transparent 25%, transparent 75%, #f0f0f0 75%, #f0f0f0);
                                background-size: 20px 20px;
                                background-position: 0 0, 10px 10px;
                            }
                            .preview-box { 
                                background: #4CAF50; 
                                opacity: 0.7; 
                                position: absolute; 
                            }
                            .info { 
                                background: #e3f2fd; 
                                padding: 15px; 
                                border-radius: 5px; 
                                margin: 10px 0; 
                            }
                            .info h3 { margin-top: 0; }
                            .dimensions { 
                                font-size: 24px; 
                                font-weight: bold; 
                                color: #2196F3; 
                            }
                            .ratio { 
                                font-size: 18px; 
                                color: #666; 
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>📐 分辨率预览</h1>
                            <div class="info">
                                <h3>尺寸信息</h3>
                                <div class="dimensions">${width} × ${height}</div>
                                <div class="ratio">长宽比: ${(width/height).toFixed(2)}:1</div>
                                <div>总像素: ${(width*height).toLocaleString()}</div>
                                <div>百万像素: ${((width*height)/1000000).toFixed(2)} MP</div>
                            </div>
                            <div class="preview-area" id="previewArea">
                                <div id="previewBox" class="preview-box"></div>
                            </div>
                            <div class="info">
                                <h3>使用建议</h3>
                                <div id="suggestion">加载中...</div>
                            </div>
                        </div>
                        <script>
                            const area = document.getElementById('previewArea');
                            const box = document.getElementById('previewBox');
                            const suggestion = document.getElementById('suggestion');
                            
                            const w = ${width};
                            const h = ${height};
                            
                            // 计算预览尺寸
                            const areaWidth = area.clientWidth;
                            const areaHeight = area.clientHeight;
                            const aspect = w / h;
                            
                            let previewWidth, previewHeight;
                            if (aspect > 1) {
                                // 横版
                                previewWidth = Math.min(areaWidth * 0.8, areaHeight * 0.8 * aspect);
                                previewHeight = previewWidth / aspect;
                            } else {
                                // 竖版或方形
                                previewHeight = Math.min(areaHeight * 0.8, areaWidth * 0.8 / aspect);
                                previewWidth = previewHeight * aspect;
                            }
                            
                            // 设置预览框
                            box.style.width = previewWidth + 'px';
                            box.style.height = previewHeight + 'px';
                            box.style.left = (areaWidth - previewWidth) / 2 + 'px';
                            box.style.top = (areaHeight - previewHeight) / 2 + 'px';
                            
                            // 生成建议
                            const mp = (w * h) / 1000000;
                            let suggestionText = '';
                            if (mp < 0.5) suggestionText = '适合图标、小图、预览图';
                            else if (mp < 2) suggestionText = '适合社交媒体、网页图片';
                            else if (mp < 5) suggestionText = '适合高清壁纸、小尺寸印刷';
                            else if (mp < 10) suggestionText = '适合4K显示、中等尺寸印刷';
                            else suggestionText = '适合大幅面印刷、专业摄影';
                            
                            suggestion.textContent = suggestionText;
                        </script>
                    </body>
                    </html>
                `);
                previewWindow.document.close();
            };
        }
    }
});