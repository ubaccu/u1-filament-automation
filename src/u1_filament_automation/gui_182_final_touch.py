"""Final UI-only polish for U1FA 1.8.2.

Keeps all existing application logic untouched. This patch only fixes home-page
navigation and modernises the calibration form controls.
"""

from __future__ import annotations

import re
from typing import Any, Callable

_STYLE_ID = "u1fa-182-final-touch"
_SCRIPT_ID = "u1fa-182-profile-picker"
_DASHBOARD_ID = "u1fa-dashboard-v20"
_FILAMENT_ID = "u1fa-filament-group"
_CALIBRATION_ID = "u1fa-calibration-card"

_CSS = r'''<style id="u1fa-182-final-touch">
/* Final navigation + form polish */
#u1fa-calibration-card select,
#u1fa-calibration-card input[type="number"],
#u1fa-calibration-card input[type="text"]{
  min-height:44px!important;
  border:1px solid #344b63!important;
  border-radius:11px!important;
  background:linear-gradient(180deg,#101923,#0b131c)!important;
  color:#eef6ff!important;
  padding:0 13px!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 7px 18px rgba(0,0,0,.08)!important;
  transition:border-color .16s ease,box-shadow .16s ease,background .16s ease!important;
}
#u1fa-calibration-card select{
  -webkit-appearance:none!important;
  appearance:none!important;
  padding-right:38px!important;
  background-image:linear-gradient(45deg,transparent 50%,#86a0ba 50%),linear-gradient(135deg,#86a0ba 50%,transparent 50%),linear-gradient(180deg,#101923,#0b131c)!important;
  background-position:calc(100% - 18px) 19px,calc(100% - 13px) 19px,0 0!important;
  background-size:5px 5px,5px 5px,100% 100%!important;
  background-repeat:no-repeat!important;
}
#u1fa-calibration-card select:focus,
#u1fa-calibration-card input:focus{
  outline:none!important;
  border-color:#32afff!important;
  box-shadow:0 0 0 3px rgba(50,175,255,.12),0 10px 24px rgba(0,0,0,.16)!important;
}
#u1fa-calibration-card select option{background:#111a23;color:#eef6ff}
#u1fa-calibration-card .u1fa-js-native-hidden{position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none!important;clip:rect(0 0 0 0)!important}
.u1fa-profile-picker{position:relative;width:100%;margin-bottom:10px}
.u1fa-profile-trigger{width:100%;min-height:48px;display:grid;grid-template-columns:36px minmax(0,1fr) 28px;align-items:center;gap:10px;text-align:left;padding:0 12px!important;border:1px solid #3d5872!important;border-radius:12px!important;background:linear-gradient(135deg,#132435,#0d1721)!important;color:#f1f7ff!important;box-shadow:0 10px 24px rgba(0,0,0,.15)!important;font-weight:800!important}
.u1fa-profile-trigger:hover{border-color:#4b83b1!important;background:linear-gradient(135deg,#162b40,#0f1a26)!important;transform:none!important}
.u1fa-profile-trigger:focus{outline:none!important;border-color:#36b2ff!important;box-shadow:0 0 0 3px rgba(54,178,255,.12),0 10px 24px rgba(0,0,0,.18)!important}
.u1fa-profile-trigger .spool{width:31px;height:31px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:#12382e;color:#49e0ad;border:1px solid rgba(73,224,173,.18)}
.u1fa-profile-trigger .spool svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.7}
.u1fa-profile-trigger .label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.u1fa-profile-trigger .chev{color:#8da5bb;font-size:15px;text-align:center;transition:transform .16s ease}
.u1fa-profile-picker.open .chev{transform:rotate(180deg)}
.u1fa-profile-menu{display:none;position:absolute;left:0;right:0;top:calc(100% + 8px);z-index:130;background:linear-gradient(180deg,#101a25,#0b131c);border:1px solid #3b5269;border-radius:14px;box-shadow:0 22px 55px rgba(0,0,0,.45);overflow:hidden}
.u1fa-profile-picker.open .u1fa-profile-menu{display:block;animation:u1faPickerIn .14s ease-out}
.u1fa-profile-picker.open-up .u1fa-profile-menu{top:auto;bottom:calc(100% + 8px)}
.u1fa-profile-search-wrap{padding:10px;border-bottom:1px solid #25384a;background:#0d1620;position:sticky;top:0;z-index:2}
.u1fa-profile-search{width:100%;height:40px!important;box-sizing:border-box;border:1px solid #30485e!important;border-radius:10px!important;background:#0a121a!important;color:#eaf4ff!important;padding:0 12px!important;outline:none}
.u1fa-profile-search:focus{border-color:#34b2ff!important;box-shadow:0 0 0 3px rgba(52,178,255,.10)!important}
.u1fa-profile-options{max-height:335px;overflow:auto;padding:7px}
.u1fa-profile-option{width:100%;display:grid;grid-template-columns:31px minmax(0,1fr) 22px;align-items:center;gap:9px;text-align:left;border:0!important;border-radius:10px!important;background:transparent!important;color:#dce8f5!important;padding:9px 10px!important;min-height:44px;box-shadow:none!important;font-weight:650!important}
.u1fa-profile-option:hover{background:#17283a!important;color:#fff!important;transform:none!important}
.u1fa-profile-option.active{background:linear-gradient(90deg,#163d5c,#162d43)!important;color:#fff!important;box-shadow:inset 3px 0 0 #35b9ff!important}
.u1fa-profile-option .dot{width:27px;height:27px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:#12352b;color:#45dca9}
.u1fa-profile-option .dot svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.7}
.u1fa-profile-option .text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;line-height:1.25}
.u1fa-profile-option .check{color:#51d9a8;font-size:14px;text-align:center}
.u1fa-profile-empty{padding:16px;text-align:center;color:#8da1b5;font-size:12px}
.u1fa-side-nav .u1fa-nav-pa span{white-space:nowrap}
@keyframes u1faPickerIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
@media(max-width:680px){.u1fa-profile-options{max-height:270px}.u1fa-profile-option .text{font-size:11px}}
</style>'''

_SCRIPT = r'''<script id="u1fa-182-profile-picker">
(function(){
  function spoolIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.4"/><path d="M5.8 8.6h12.4M5.8 15.4h12.4"/></svg>';}
  function enhance(){
    var select=document.querySelector('#u1fa-calibration-card select[name="profile_name"]') || document.querySelector('#u1fa-filament-group select[name="profile_name"]');
    if(!select || select.dataset.u1faEnhanced==='1') return;
    select.dataset.u1faEnhanced='1';
    var picker=document.createElement('div'); picker.className='u1fa-profile-picker';
    var trigger=document.createElement('button'); trigger.type='button'; trigger.className='u1fa-profile-trigger';
    trigger.setAttribute('aria-haspopup','listbox'); trigger.setAttribute('aria-expanded','false');
    trigger.innerHTML='<span class="spool">'+spoolIcon()+'</span><span class="label"></span><span class="chev">⌄</span>';
    var menu=document.createElement('div'); menu.className='u1fa-profile-menu';
    var searchWrap=document.createElement('div'); searchWrap.className='u1fa-profile-search-wrap';
    var search=document.createElement('input'); search.type='search'; search.className='u1fa-profile-search'; search.placeholder='Cerca filamento / Search filament…';
    searchWrap.appendChild(search);
    var optionsBox=document.createElement('div'); optionsBox.className='u1fa-profile-options'; optionsBox.setAttribute('role','listbox');
    menu.appendChild(searchWrap); menu.appendChild(optionsBox); picker.appendChild(trigger); picker.appendChild(menu);
    select.parentNode.insertBefore(picker,select); select.classList.add('u1fa-js-native-hidden');

    function selectedText(){var o=select.options[select.selectedIndex]; return o ? o.text : '—';}
    function render(filter){
      var q=(filter||'').trim().toLowerCase(); optionsBox.innerHTML=''; var shown=0;
      Array.prototype.forEach.call(select.options,function(opt,index){
        if(q && opt.text.toLowerCase().indexOf(q)<0) return;
        shown++;
        var item=document.createElement('button'); item.type='button'; item.className='u1fa-profile-option'+(index===select.selectedIndex?' active':'');
        item.setAttribute('role','option'); item.setAttribute('aria-selected',index===select.selectedIndex?'true':'false');
        item.innerHTML='<span class="dot">'+spoolIcon()+'</span><span class="text"></span><span class="check">'+(index===select.selectedIndex?'✓':'')+'</span>';
        item.querySelector('.text').textContent=opt.text;
        item.addEventListener('click',function(){select.selectedIndex=index; select.dispatchEvent(new Event('change',{bubbles:true})); close();});
        optionsBox.appendChild(item);
      });
      if(!shown){var empty=document.createElement('div'); empty.className='u1fa-profile-empty'; empty.textContent='Nessun filamento trovato / No filament found'; optionsBox.appendChild(empty);}
    }
    function sync(){trigger.querySelector('.label').textContent=selectedText(); render(search.value);}
    function open(){
      picker.classList.add('open'); trigger.setAttribute('aria-expanded','true'); render(search.value);
      picker.classList.remove('open-up');
      var r=trigger.getBoundingClientRect(); if(window.innerHeight-r.bottom<390 && r.top>390) picker.classList.add('open-up');
      setTimeout(function(){search.focus();},0);
    }
    function close(){picker.classList.remove('open','open-up'); trigger.setAttribute('aria-expanded','false'); search.value=''; sync();}
    trigger.addEventListener('click',function(){picker.classList.contains('open')?close():open();});
    search.addEventListener('input',function(){render(search.value);});
    search.addEventListener('keydown',function(e){if(e.key==='Escape'){close();trigger.focus();}});
    select.addEventListener('change',sync);
    document.addEventListener('click',function(e){if(!picker.contains(e.target)) close();});
    sync();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance); else enhance();
})();
</script>'''


def _merge_sidebar_filament_calibration(page: str, language: str) -> str:
    if language == "en":
        page = page.replace("<span>Filaments</span>", "<span>Filaments &amp; PA</span>", 1)
        label = "Calibration"
    else:
        page = page.replace("<span>Filamenti</span>", "<span>Filamenti &amp; PA</span>", 1)
        label = "Calibrazione"
    pattern = re.compile(
        rf'<a[^>]*>\s*<svg.*?</svg>\s*<span>{re.escape(label)}</span>\s*</a>',
        re.DOTALL,
    )
    return pattern.sub("", page, count=1)


def _fix_system_targets(page: str) -> str:
    page = page.replace(
        'href="#u1fa-system-group" data-u1fa-jump="u1fa-system-group"',
        f'href="#{_DASHBOARD_ID}" data-u1fa-jump="{_DASHBOARD_ID}"',
    )
    page = page.replace(
        'href="#u1fa-system-group"',
        f'href="#{_DASHBOARD_ID}" data-u1fa-jump="{_DASHBOARD_ID}"',
    )
    return page


def final_touch(page: str, language: str = "it") -> str:
    page = _merge_sidebar_filament_calibration(page, language)
    page = _fix_system_targets(page)
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace("</head>", _CSS + "</head>", 1)
    if f'id="{_SCRIPT_ID}"' not in page:
        page = page.replace("</body>", _SCRIPT + "</body>", 1)
    return page


def install_182_final_touch(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_182_final_touch", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return final_touch(page, language)

    setattr(patched, "_u1fa_182_final_touch", True)
    gui_module._home = patched
