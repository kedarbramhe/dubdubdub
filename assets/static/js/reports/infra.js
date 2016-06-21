'use strict';
(function() {
    var utils;
    var repUtils;
    klp.init = function() {
        utils = klp.boundaryUtils;
        repUtils = klp.reportUtils;
        klp.router = new KLPRouter();
        klp.router.init();
        fetchReportDetails();
        klp.router.start();
    };

    var preschoolInfraHash = {
        'ang-drinking-water': {
            display: 'Drinking Water',
            icon: ['fa  fa-tint']
        },
        'ang-toilet-for-use': {
            display:'Toilets',
            icon: ['fa fa-male', 'fa fa-female']
        },
        'ang-bvs-present': {
            display: 'Functional Bal Vikas Samithis',
            icon: ['fa fa-users']
        },
        'ang-separate-handwash': {
            display: 'Separate Hand-Wash',
            icon: ['fa fa-hand-o-up']
        },
        'ang-activities-use-tlm': {
            display: 'Uses Learning Material',
            icon: ['fa fa-cubes']
        },
        'ang-in-spacious-room': {
            display: 'Spacious Room',
            icon: ['fa fa-arrows-alt']
        }
    };

    var schoolInfraHash = {
        'sum_has_playground': {
            'icon': ['fa fa-futbol-o'],
            'display': 'Playground'
        },
        'sum_has_drinking_water': {
            'icon': ['fa fa-tint'],
            'display': 'Drinking Water',
        },
        'sum_has_toilet': {
            'icon': ['fa fa-male', 'fa fa-female'],
            'display': 'Toilets'
        },
        'sum_has_library': {
            'icon': ['fa fa-book'],
            'display': 'Library'
        },
        'sum_has_boundary_wall': {
            'icon': ['fa fa-circle-o-notch'],
            'display': 'Secure Boundary Wall'
        },
        'sum_has_electricity': {
            'icon': ['fa fa-plug'],
            'display': 'Electricity'
        },
        'sum_has_computer': {
            'icon': ['fa fa-laptop'],
            'display': 'Computers'
        },
        'sum_has_mdm': {
            'icon': ['fa fa-spoon'],
            'display': 'Mid-Day Meal'
        },
        'sum_has_toilet_girls': {
            'icon': ['fa fa-female'],
            'display': 'Separate Girls\' Toilets'
        },
        'sum_has_classrooms_in_good_condition': {
            'icon': ['fa fa-users'],
            'display': 'Good Classrooms'
        },
        'sum_has_blackboard': {
            'icon': ['fa fa-square'],
            'display': 'Blackboards'
        }
    };

    function fetchReportDetails()
    {
        var repType,bid,lang;
        repType = repUtils.getSlashParameterByName("report_type");
        bid = repUtils.getSlashParameterByName("id");
        lang = repUtils.getSlashParameterByName("language");

        var url = "reports/dise/"+repType+"/?language="+lang+"&id="+bid;
        var $xhr = klp.api.do(url);
        $xhr.done(function(data) {
            console.log('data', data);
            var schooltype = "Schools";
            var summaryJson = getSummaryData(data);
            renderSummary(summaryJson, schooltype);
            if ( data["btype"] == 2 ){
                schooltype = "PreSchool";
                var comparisonJSON = data["comparison"]["year-wise"];
                renderComparison(comparisonJSON, preschoolInfraHash);
                var neighboursJSON = data["comparison"]["neighbours"];
                renderNeighbours(neighboursJSON, preschoolInfraHash);
            }
            else
            {
                fetchSchoolData(data);
            }
        });
    }

    function fetchSchoolData(data)
    {
        var acadYear = data["boundary_info"]["academic_year"].replace(/20/g, '');
        klp.dise_api.queryBoundaryName(data["boundary_info"]["name"], data["boundary_info"]["type"],acadYear).done(function(diseData) {
            if( diseData.length != 0 )
            {
                var boundary = diseData[0].children[0];
                klp.dise_api.getBoundaryData(boundary.id, boundary.type, acadYear).done(function(diseData) {
                    console.log('summary diseData', diseData);
                    renderGrantSummary(diseData);
                })
                .fail(function(err) {
                    klp.utils.alertMessage("Sorry, could not fetch programmes data", "error");
                });
            }
        })
        .fail(function(err) {
            klp.utils.alertMessage("Sorry, could not fetch programmes data", "error");
        });
        getNeighbourData(data, acadYear);
        var yearData = []; 
        yearData[acadYear] = data["academic_year"];
        var years = acadYear.split("-").map(Number);
        yearData[(years[0]-1).toString()+"-"+(years[1]-1).toString()] = "20"+(years[0]-1).toString()+"-"+"20"+(years[1]-1).toString();
        yearData[(years[0]-2).toString()+"-"+(years[1]-2).toString()] = "20"+(years[0]-2).toString()+"-"+"20"+(years[1]-2).toString();        
        var passYearData = {"name": data["boundary_info"]["name"], "type": data["boundary_info"]["type"]};
        getMultipleData(yearData, passYearData, getLoopData, renderComparison,"acadYear");
        
    }

    function getNeighbourData(data, acadYear)
    {
        var type = data["boundary_info"]["type"];
        if(type == "district")
        {
            klp.dise_api.getMultipleBoundaryData(null, null, type, acadYear).done(function(diseData) {
                console.log('neighbours diseData', diseData);
                renderNeighbours(diseData["results"]["features"],schoolInfraHash);
            })
            .fail(function(err) {
                klp.utils.alertMessage("Sorry, could not fetch programmes data", "error");
            });
        }
        else
        {
            klp.dise_api.queryBoundaryName(data["boundary_info"]["parent"]["name"], data["boundary_info"]["parent"]["type"],acadYear).done(function(diseData) {
                var boundary = diseData[0].children[0];
                klp.dise_api.getMultipleBoundaryData(boundary.id, boundary.type, type, acadYear).done(function(diseData) {
                    console.log('neighbours diseData', diseData);
                    renderNeighbours(diseData["results"]["features"],schoolInfraHash);
                })
                .fail(function(err) {
                    klp.utils.alertMessage("Sorry, could not fetch programmes data", "error");
                });
            })
            .fail(function(err) {
                klp.utils.alertMessage("Sorry, could not fetch programmes data", "error");
            });
        }
    }

    function getMultipleData(inputData, passedData, getData, exit,iteratorName)
    {
        var numberOfIterations = Object.keys(inputData).length;
        var outputData= {};
        var index = 0,
            done = false,
            shouldExit = false;
        var loop = {
            next:function(){
                if(done){
                    if(shouldExit && exit){
                        return exit(outputData,schoolInfraHash); // Exit if we're done
                    }
                }
                if(index <  numberOfIterations){
                    index++; // Increment our index
                    getData(loop); // Run our process, pass in the loop
                }
                else {
                    done = true; // Make sure we say we're done
                    if(exit)
                        exit(outputData,schoolInfraHash); // Call the callback on exit
                }
            },
            iteration:function(){
                passedData[iteratorName] = Object.keys(inputData)[index-1];
                passedData["value"] = inputData[passedData[iteratorName]];
                return passedData; // Return the loop number we're on
            },
            addData:function(diseData){
                outputData[Object.keys(inputData)[index-1]] = diseData;
            },
            break:function(end){
                done = true; // End the loop
                shouldExit = end; // Passing end as true means we still call the exit callback
            }
        };
        loop.next();
        return loop;
    }

    function getLoopData(loop)
    {
        var data = loop.iteration();
        klp.dise_api.queryBoundaryName(data["name"], data["type"], data["acadYear"]).done(function(diseNameData) {
            if( diseNameData.length == 0)
            {
                loop.next();
                return;
            }
            var boundary = diseNameData[0].children[0];
            klp.dise_api.getBoundaryData(boundary.id, boundary.type, data["acadYear"]).done(function(diseData) {
                console.log('diseData', diseData);
                loop.addData(diseData);
                loop.next();
            })
            .fail(function(err) {
                klp.utils.alertMessage("Sorry, could not fetch programmes data", "for neighbour"+neighbour);
            });
        })
        .fail(function(err) {
            klp.utils.alertMessage("Sorry, could not fetch name data", "error");
        });
    }


    function getSummaryData(data)
    {
        var summaryJSON = {
            "boundary"  : data["boundary_info"],
            "school_count" : data["summary_data"]["num_schools"],
            "teacher_count" : data["summary_data"]["teacher_count"],
            "gender" : data["summary_data"]["gender"],
            "student_total": data["summary_data"]["num_students"]
        };

        return summaryJSON;
    }



    function loadData(schoolType, params) {

        /*var dataURL = "reports/infrastructure/xxx";
        var $dataXHR = klp.api.do(detailURL, params);
        $datadetailXHR.done(function(data) {*/
            var grantdata = { 
                "received": {
                    "sg_perc": 25,
                    "sg_amt": 350000,
                    "smg_perc": 65,
                    "smg_amt": 550000,
                    "tlm_perc": 10,
                    "tlm_amt": 60000   
                },
                "teacher_count": 120,
                "student_total":48000
            };
            renderGrantSummary(grantdata);

    }


    function renderSummary(data, schoolType) {
        var tplTopSummary = swig.compile($('#tpl-topSummary').html());
        var tplReportDate = swig.compile($('#tpl-reportDate').html());
        
        var now = new Date();
        var today = {'date' : moment(now).format("MMMM D, YYYY")};
        var dateHTML = tplReportDate({"today":today});
        $('#report-date').html(dateHTML);

        data['student_total'] = data["gender"]["boys"] + data["gender"]["girls"];
        if (data["teacher_count"] == 0)
            data['ptr'] = "NA";
        else
            data['ptr'] = Math.round(data["student_total"]/data["teacher_count"]);
        data['girl_perc'] = Math.round(( data["gender"]["girls"]/data["student_total"] )* 100);
        data['boy_perc'] = 100-data['girl_perc'];
        
        var topSummaryHTML = tplTopSummary({"data":data});
        $('#top-summary').html(topSummaryHTML);

    }

    function renderGrantSummary(data){
        var tpl = swig.compile($('#tpl-grantSummary').html());
        var total = data.properties["sum_school_dev_grant_recd"] + data.properties["sum_tlm_grant_recd"];
        var received = {
                        "sdg":data.properties["sum_school_dev_grant_recd"],
                        "tlm": data.properties["sum_tlm_grant_recd"],
                        "total": total,
                        "per_student": total/(data.properties["sum_girls"]+data.properties["sum_boys"]),
                        "per_teacher": data.properties["sum_tlm_grant_recd"]/(data.properties["sum_graduate_teachers"]+data.properties["sum_head_teacher"])
        };
        var html = tpl({"received":received});
        $('#grant-summary').html(html);
    }

    function renderComparison(data, hash) {
        var transpose = transposeData(data, hash);
        var tplYearComparison = swig.compile($('#tpl-YearComparison').html());
        var yrcompareHTML = tplYearComparison({"transpose":transpose});
        $('#comparison-year').html(yrcompareHTML);
    }

    function renderNeighbours(data,hash) {
        var percData = {"keys":{}};
        
        for (var each in data) {
            for (var key in data[each]["properties"]) {
                var iconTag = "";
                if(key != "name" && key != "school_count" && key in hash) {
                    for(var i in hash[key]['icon']){
                        iconTag += "<span class='" + hash[key]['icon'][i] + "'></span>   ";
                    }
                    if (!percData["keys"][key])
                        percData["keys"][key] = {"icon":iconTag,"name":hash[key]['display']};
                    if(!percData[data[each]["id"]])
                        percData[data[each]["id"]] = {"name": data[each]["id"]};
                    percData[data[each]["id"]][hash[key]['display']]= {"perc": (data[each]["properties"][key]/data[each]["properties"]["sum_schools"]) * 100};
                }
            }
        }
        var tplComparison = swig.compile($('#tpl-neighComparison').html());
        var compareHTML = tplComparison({"neighbours":percData});
        $('#comparison-neighbour').html(compareHTML);
    }

    function transposeData(data,hash) {
        var transpose = {
            "year": [],
            "school_count" : {},
            "Basic Infrastructure" : { "name":"Basic Infrastructure"},
            "Learning Environment" : { "name":"Learning Environment"},
            "Nutrition and Hygiene" : { "name":"Nutrition and Hygiene"},
            "Toilets" : { "name":"Toilets"}
        };

        var basic_infra = ["sum_has_boundary_wall","sum_has_playground","sum_has_electricity","sum_has_classrooms_in_good_condition"];
        var learning_env = ["sum_has_blackboard","sum_has_computer","sum_has_library"];
        var nut_hyg = ["sum_has_mdm","sum_has_drinking_water"];
        var toilets = ["sum_has_toilet","sum_has_toilet_girls"];

        for (var truncyear in data) {
            var year = data[truncyear]["year"];
            transpose["year"].push(year);
            transpose["school_count"][year] = data[truncyear]["properties"]["sum_schools"];
            var infraData = data[truncyear]["properties"];
            for (var key in infraData) {
                var iconTag = "";
                if(key != "year" && key != "school_count" && key in hash)
                {
                    for(var i in hash[key]['icon']){
                        iconTag += "<span class='" + hash[key]['icon'][i] + "'></span>   ";
                    }
                }
                if ($.inArray(key,basic_infra) != -1 ) {
                    if(!transpose["Basic Infrastructure"][key])
                        transpose["Basic Infrastructure"][key] = {"name":hash[key]['display'],"icon":iconTag};
                    transpose["Basic Infrastructure"][key][year] = (infraData[key]/infraData["sum_schools"]*100);

                    
                } else if ($.inArray(key,learning_env) != -1) {
                    if(!transpose["Learning Environment"][key])
                        transpose["Learning Environment"][key] = {"name":hash[key]['display'],"icon":iconTag};
                    transpose["Learning Environment"][key][year] = (infraData[key]/infraData["sum_schools"]*100);
                } else if ($.inArray(key,nut_hyg) != -1) {
                    if(!transpose["Nutrition and Hygiene"][key])
                        transpose["Nutrition and Hygiene"][key] = {"name":hash[key]['display'],"icon":iconTag};
                    transpose["Nutrition and Hygiene"][key][year] = (infraData[key]/infraData["sum_schools"]*100);
                } else if ($.inArray(key,toilets) != -1) {
                    if(!transpose["Toilets"][key])
                        transpose["Toilets"][key] = {"name":hash[key]['display'],"icon":iconTag};
                    transpose["Toilets"][key][year] = (infraData[key]/infraData["sum_schools"]*100);
                } else {}
            }
        }
        transpose["year"].sort();
        return transpose;
    }



})();

