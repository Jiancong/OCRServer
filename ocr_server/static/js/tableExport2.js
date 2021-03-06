
    var tablesToExcel = (function() {
      var uri = 'data:application/vnd.ms-excel;base64,'
      , tmplWorkbookXML = '<?xml version="1.0"?><?mso-application progid="Excel.Sheet"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">'
        + '<DocumentProperties xmlns="urn:schemas-microsoft-com:office:office"><Author>Axel Richter</Author><Created>{created}</Created></DocumentProperties>'
        + '<Styles>'
        + '<Style ss:ID="Currency"><NumberFormat ss:Format="Currency"></NumberFormat></Style>'
        + '<Style ss:ID="Date"><NumberFormat ss:Format="Medium Date"></NumberFormat></Style>'
        + '</Styles>' 
        + '{worksheets}</Workbook>'
      , tmplWorksheetXML = '<Worksheet ss:Name="{nameWS}"><Table>{rows}</Table></Worksheet>'
      , tmplCellXML = '<Cell{attributeStyleID}{attributeFormula}><Data ss:Type="{nameType}">{data}</Data></Cell>'
      , base64 = function(s) { return window.btoa(unescape(encodeURIComponent(s))) }
      , format = function(s, c) { return s.replace(/{(\w+)}/g, function(m, p) { return c[p]; }) }
      return function(tables, wsnames, wbname, appname) {
        var ctx = "";
        var workbookXML = "";
        var worksheetsXML = "";
        var rowsXML = "";
  
        for (var i = 0; i < tables.length; i++) {
          if (!tables[i].nodeType) tables[i] = document.getElementById(tables[i]);
          for (var j = 0; j < tables[i].rows.length; j++) {
            var rowsData = '';
            for (var k = 0; k < tables[i].rows[j].cells.length; k++) {
              if(k == 0){
                if(j >= 1){
                  var check1 = document.getElementsByName("checkItem")[j-1];
                  //console.log(check1);
                  //console.log(check1.checked);
                  if(!check1.checked){
                    //console.log("break");
                    break;
                  }
                }
                continue;
              }
              var dataType = tables[i].rows[j].cells[k].getAttribute("data-type");
              var dataStyle = tables[i].rows[j].cells[k].getAttribute("data-style");
              var dataValue = tables[i].rows[j].cells[k].getAttribute("data-value");
              dataValue = (dataValue)?dataValue:tables[i].rows[j].cells[k].innerHTML;
/*
              console.log("row:" + j + ",cell:" + k +",dataType:" + dataType
                  //+ ", dataStyle:" + dataStyle
                  + ", dataValue:" + dataValue.toString());
*/
              if(j == 1 && k == 1 && dataValue.indexOf("matching") > 0){
                break;
              }
              // if(dataValue.indexOf("input")>0){
              /*
              if(k == 0){
                console.log("row:" + j + ",cell:" + k +",dataType:" + dataType
                  + ", dataStyle:" + dataStyle
                  + ", dataValue:" + dataValue);
                //var check2 = document.getElementsByName("checkItem")[j-1];
               //console.log(check2);
                continue;
              }
              */
              var dataFormula = tables[i].rows[j].cells[k].getAttribute("data-formula");
              dataFormula = (dataFormula)?dataFormula:(appname=='Calc' && dataType=='DateTime')?dataValue:null;
              ctx = {  attributeStyleID: (dataStyle=='Currency' || dataStyle=='Date')?' ss:StyleID="'+dataStyle+'"':''
                     , nameType: (dataType=='Number' || dataType=='DateTime' || dataType=='Boolean' || dataType=='Error')?dataType:'String'
                     , data: (dataFormula)?'':dataValue
                     , attributeFormula: (dataFormula)?' ss:Formula="'+dataFormula+'"':''
                    };
              rowsData += format(tmplCellXML, ctx);
            }
            if(rowsData.length > 0)
              rowsXML = rowsXML + '<Row>' + rowsData + '</Row>';
          }
          ctx = {rows: rowsXML, nameWS: wsnames[i] || 'Sheet' + i};
          worksheetsXML += format(tmplWorksheetXML, ctx);
          rowsXML = "";
        }
        
        ctx = {created: (new Date()).getTime(), worksheets: worksheetsXML};
        workbookXML = format(tmplWorkbookXML, ctx);
  
        //console.log(workbookXML);
  
        var link = document.createElement("A");
        link.href = uri + base64(workbookXML);
        link.download = wbname || 'invoice.xls';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        }
      })();