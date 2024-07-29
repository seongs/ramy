
// 작성 버튼 눌렀을 떄
$('#btn-primary').click(write);

function write() {
    //백에서 필요한 객체 (파라미터들)
    let diary = {
        "dialy_id":1,
        "user_id":1,
        "content": $(".text-container").val(),   //바뀔 수 있는 부분
        " content_index":"ssssss",
        "created_at":"Date.now",
        "summary":"test"
    };
   console.log($(".text-container").val());
    //전송
    $.ajax({
        type: 'POST',       //바뀔 수 있는 부분
        url: `http://127.0.0.1:8000/diaries`, // 백주소//바뀔 수 있는 부분
        dataType: 'json', // 프론트가 받을 데이터 형식
        contentType: 'application/json', // 백으로 보낼 데이터 형식
        data: JSON.stringify(diary), //백으로 보낼 데이터
        success: function (result) {
            console.log(result)
            // localStorage.setItem("diary-info", JSON.stringify(result));
            // window.location.href('')
        },
        error: function (result, status, error) {
            console.log(error)
        }
    })
}