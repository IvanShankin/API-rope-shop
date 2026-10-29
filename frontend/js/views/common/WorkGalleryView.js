export class WorkGalleryView {
  constructor(root) {
    const photos = Array.from(root.querySelectorAll('.work-gallery__photo'));
    const dialog = root.querySelector('dialog');
    if (!dialog || !photos.length) return;
    const image=dialog.querySelector('.work-gallery__full-image');
    const caption=dialog.querySelector('.work-gallery__current');
    const description=document.createElement('p');description.className='work-gallery__description';description.setAttribute('data-no-translate','');description.hidden=true;image.after(description);
    const more=root.querySelector('[data-gallery-more]');
    const pageSize=Number(root.dataset.galleryPageSize)||10;
    let visible=pageSize,current=0,opener;
    const update=()=>{photos.forEach((photo,i)=>{photo.hidden=i>=visible;});if(more)more.hidden=visible>=photos.length;};
    more?.addEventListener('click',()=>{const first=photos[visible];visible+=pageSize;update();first?.focus({preventScroll:true});});
    update();
    const show=index=>{
      current=(index+photos.length)%photos.length;
      const source=photos[current].querySelector('img');
      image.src=source.src;image.alt=source.alt;
      description.textContent=photos[current].dataset.description||'';description.hidden=!description.textContent;
      caption.textContent=`${current+1} / ${photos.length}`;
    };
    photos.forEach((photo,i)=>photo.addEventListener('click',()=>{opener=photo;show(i);dialog.showModal();document.body.classList.add('page__body--locked');}));
    dialog.addEventListener('close',()=>{document.body.classList.remove('page__body--locked');opener?.focus({preventScroll:true});});
    dialog.querySelector('.work-gallery__close').addEventListener('click',()=>dialog.close());
    dialog.querySelector('[data-photo-prev]').addEventListener('click',()=>show(current-1));
    dialog.querySelector('[data-photo-next]').addEventListener('click',()=>show(current+1));
    dialog.addEventListener('keydown',event=>{
      if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();show(current+(event.key==='ArrowLeft'?-1:1));}
    });
    dialog.addEventListener('click',event=>{
      if(event.target!==dialog)return;
      const rect=dialog.getBoundingClientRect();
      if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close();
    });
  }
}
