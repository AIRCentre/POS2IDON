
# Use packages
begin
	import DataFrames
	import DecisionTree
	using JLD2
	import Pandas
end

"""
This function perform the prediction of the input dataframe created
in the python function "Create_SCMap_Julia". The pandas dataframe from python is converted
in a Julia DataFrame and to matrix on which the prediction is done.
Input: RFModelFolderPath - Path of the folder.
	   Julia RF_model    - String
	   Python DataFrame to predict - Pandas DataFrame
Output: Classified Results
"""
function Classification_Julia(RFmodelFolder,DFtoPredictWithoutNaN,RF_model_jl)
	# Load ML model
	@load joinpath(RFmodelFolder, RF_model_jl) RF_model;
	# Convert Pandas DataFrame to Julia DataFrame
	DFtoPredictWithoutNaN_jl = DataFrames.DataFrame(Pandas.DataFrame(DFtoPredictWithoutNaN))
	# Matrix to predict without NaNs
	MatrixToPredictWithoutNaN = convert(Matrix{Float64}, Matrix(DFtoPredictWithoutNaN_jl));
	# Predict using model
	t = time()
	ClassiResults = DecisionTree.apply_forest(RF_model, MatrixToPredictWithoutNaN);
	dt = time() - t
	return ClassiResults,dt
end