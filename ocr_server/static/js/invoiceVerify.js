function getInvocieInfo(user_id, taskid, textInvocetype) {

    $.ajax({
        type: 'GET',
        dataType: 'json', // 数据类型配置成jsonp
        //jsonp : "callback", //配置jsonp随机码标签,在服务器代码部分需要用到他来拼接一个json的js对象
        //url : 'https://aip.baidubce.com/rest/2.0/ocr/v1/general', //http://10.26.6.222:5000/api/detect_in', //服务路径
        url: 'http://180ly66419.iok.la:5000/api/detect_in?1=1&user_id=' + user_id + '&task_id=' + taskid,
        // url: 'test.json',
        async: false,
        timeout: 5,
        data: {
            q: "select * from json where url=\"http://www.w3dev.cn/json.asp\"",
            format: "json"
        },

        success: function (response) {
            responseData = JSON.stringify(response);
            var obj = eval('(' + responseData + ')');
            invoiceID = obj.data['invoice_code'];
            invoiceNo = obj.data['invoice_num'];

        },
        error: function () {
            alert('服务器异常，获取发票信息失败！');
        }
    });
    if (textInvocetype == "textInvoiceNum") {
        return invoiceNo;
    }
    else if (textInvocetype == "textInvoiceID") {
        return invoiceID;
    }
}

function getTaskList(user_id) {
    var taskList = []
    $.ajax({
        type: 'GET',
        dataType: 'json', // 数据类型配置成jsonp
        //jsonp : "callback", //配置jsonp随机码标签,在服务器代码部分需要用到他来拼接一个json的js对象
        url: "http://180ly66419.iok.la:5000/api/fetch/records?user_id=" + user_id,
        async: false,
        timeout: 5,
        headers: {
            'Access-Control-Allow-Origin': '*',
        },

        jsonp: "callback",
        jsonpCallback: "jsonpCallback",
        statusCode: {
            504: function () {
                alert("暂无发票数据");
            },
        },

        success: function (response) {
            //alert("enter success!");

            responseData = JSON.stringify(response);
            var obj = eval('(' + responseData + ')');
            //alert(typeof(obj))
            //alert( obj.data["task_id_list"]);
            var tastListStr = obj.data["task_id_list"];
            var tasklistObj = tastListStr.slice(1, -1).split(",");
            for (let i in tasklistObj) {
                if (i == 0) {
                    taskList.push(tasklistObj[i].slice(1, -1));
                }
                else {
                    taskList.push(tasklistObj[i].slice(2, -1));
                }
            }
            //alert(taskList +typeof (taskList)+ taskList[4] + taskList.length);
        },

        error: function () {
            alert('服务器异常，获取发票列表失败！' + response.status);
        }
    });
    //alert(taskList);
    return taskList;
}


function getInvoiceBase64(user_id, taskId, invocetype) {
    $.ajax({
        type: 'GET',
        dataType: 'json', // 数据类型配置成jsonp
        //url: 'http://180ly66419.iok.la:5000/api/detect_in?1=1&user_id=2&task_id=a999c07fe9b703be05286029e5a2dd0e', //服务路径
        url: "http://180ly66419.iok.la:5000/api/detect_in?1=1&user_id=" + user_id + "&task_id=" + taskId, //服务路径
        async: false,
        timeout: 5,
        headers: {
            'Access-Control-Allow-Origin': '*',
        },

        jsonp: "callback",
        jsonpCallback: "jsonpCallback",

        success: function (response) {
            responseData = JSON.stringify(response);
            var obj = eval('(' + responseData + ')');
            imgNumBase64 = obj.data["invoice_num_encode"];
            imgIDBase64 = obj.data["invoice_code_encode"];

            //alert(imgSrc);

        },
        error: function () {
            alert('服务器异常，获取图片失败！');
        }
    });
    if (invocetype == "invoiceNum") {
        return imgNumBase64;
    }
    else if (invocetype == "invoiceID") {
        return imgIDBase64;
    }
}


function getTasklistNum(user_id) {

    var num = getTaskList(user_id);
    return getTaskList(user_id).length;

}

function getImgBase64(task_id) {
    $.ajax({
        url: "http://180ly66419.iok.la:5000/api/fetch/image?1=1&task_id=" + task_id,
        type: 'GET',
        dataType: 'json', // 数据类型配置成jsonp
        async: false,
        timeout: 5,
        headers: {
            'Access-Control-Allow-Origin': '*',
        },

        jsonp: "callback",
        jsonpCallback: "jsonpCallback",

        success: function (response) {
            responseData = JSON.stringify(response);
            var obj = eval('(' + responseData + ')');
            imgBase64 = obj.data["imageb64"];
        },
        error: function () {
            alert('服务器异常，获取发票大图失败！');
        }
    });

    return imgBase64;

}

function showNumAndID(user_id, taskId) {
    //get invoice num and  ID pic
    var baseURl = "data:image/png;base64,";
    document.images.invoiceNum.src = baseURl + getInvoiceBase64(user_id, taskId, "invoiceNum");
    document.images.invoiceID.src = baseURl + getInvoiceBase64(user_id, taskId, "invoiceID");
    document.images.imgShow.src = baseURl + getImgBase64(taskId);
    //get invoice info
    invoiceTextID = getInvocieInfo(user_id, taskId, "textInvoiceID");
    invoiceTextNum = getInvocieInfo(user_id, taskId, "textInvoiceNum");
    $("#textInvoiceID").val(invoiceTextID);
    $("#textInvoiceNum").val(invoiceTextNum);

}

function getAllInvoceInfo(user_id) {

    var taskList = getTaskList(user_id);
    var invoiceInfoList = [];

    for (i = 0; i < tasklist.length; i++) {
        var invoiceInfo = {};
        invoiceInfo["taskId"] = tasklist[i];
        invoiceInfo["invoiceTextID"] = getInvocieInfo(user_id, taskList[i], "textInvoiceID");
        invoiceInfo["invoiceTextNum"] = getInvocieInfo(user_id, taskList[i], "textInvoiceNum");
        invoiceInfoList.push(invoiceInfo)
    }
    var jsonString = JSON.stringify(invoiceInfoList);
    var epc = eval("(" + jsonString + ")");
    alert(epc[2].taskId);
}

