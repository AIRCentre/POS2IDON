# # install packages
# import Pkg; Pkg.add("Flux")
# import Pkg; Pkg.add("BSON")
# import Pkg; Pkg.add("Glob")
# import Pkg; Pkg.add("CUDA")


# # import packages
using Flux
using BSON
using Glob
using CUDA

# println(CUDA.functional())
# println(Flux.GPU_BACKEND)
##################################################

cat_channels(mx,x) = cat(mx, x, dims=3)

"""
This function load the model of julia
Input: UNETModelFolderPath - Path of the folder.
"""
function Load_Julia_Model(model_folder)

    model_path = glob("$(model_folder)/*.bson")[1]
    BSON.@load (model_path) model_cpu mean_bands_cpu std_bands_cpu lr nepochs batchsize nclasses

    model = model_cpu
    mean_bands = mean_bands_cpu
    std_bands = std_bands_cpu

    # check in GPU is available
    if CUDA.functional()
        device = gpu
        println("(using GPU)")
    else
        device = cpu
        println("(using CPU)")
    end

    return device, model,mean_bands,std_bands
end

# function Load_Julia_Model(model_folder)

#     model_path = glob("$(model_folder)/*.bson")[1]
#     BSON.@load (model_path) model_cpu mean_bands_cpu std_bands_cpu lr nepochs batchsize nclasses

#     device = cpu
#     model = model_cpu |> device
#     mean_bands = mean_bands_cpu |> device
#     std_bands = std_bands_cpu |> device

#     return device,model,mean_bands,std_bands

# end


"""
This function perform the prediction of the input image patch processed 
in the python function "unet_predition_julia".
Input: Image to predict    - Array{Float32, 3}
        JuliaUnet_model,mean_bands,std_bands    - String
Output: Prediction Results
"""

function Classification_Julia(device, img, model, mean_bands, std_bands)
    # check in GPU is available
    if device == gpu
        img = cu(img)
    else
        device == cpu
    end

    # load model on device
    model = model |> device
    mean_bands = mean_bands |> device
    std_bands = std_bands |> device

    # normalization
    img = (img .- mean_bands) ./ std_bands
    # reshape the array to add a new dimension of size 1
    bands=reshape(img, (size(img, 1), size(img, 2), size(img, 3), 1)) |> device
	# predict using model
    logits = model(bands)
    # reorder the dimensions to (1, 11, 256, 256)
    logits = permutedims(logits, (4, 3, 1, 2))
    
	return logits
end

