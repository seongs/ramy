const { pic, content, date } = JSON.parse(localStorage.getItem("diary-info"));
localStorage.remove("user-info");

var str = '';
str += `<div class="frame-a">
<!-- 버튼 -->
<img src="png/x.png" alt="Close">

<!-- 빈 공간 -->
<div class="empty-space">
  <div class="text-content">
    <span class="date">${date}</span>
  </div>       

</div>
</div>
<div class="image-container">
<img src="${pic}" alt="Diary Entry"> 
</div>

<div class="text-container">
<div class="text-box">
  ${content}
</div>
</div>`

$("#diary-content").append(str);


