psql -U klp -d dubdubdub -f sql/assessment-aggregation/gradeassessment-aggregates.sql
echo "Finished grade assessment aggregates"
psql -U klp -d dubdubdub -f sql/assessment-aggregation/createnewassessments_pid53-56.sql
echo "Finished creating new grade assessments"
psql -U klp -d dubdubdub -f sql/assessment-aggregation/fillgradeassessment-aggregates.sql
echo "Finished fill grade assessments"
psql -U klp -d dubdubdub -f sql/assessment-aggregation/fillgradepercentile.sql
echo "Finished grade percentile"
psql -U klp -d dubdubdub -f sql/assessment-aggregation/assessment-aggregation_pid53-56.sql
echo "Finished creating functions for pid 53-56"
psql -U klp -d dubdubdub -f sql/assessment-aggregation/fillassessments_pid53-56.sql
echo "Finished grade percentile for newly created assessments"
