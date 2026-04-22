# 插值-逆解-后续提取视频和梯度下降共用的环境

# 虚拟环境创建
conda env create -f environment.yml
conda activate gvhmr

# 有cuda环境前提下，安装PyTorch3D
pip install "git+https://github.com/facebookresearch/pytorch3d.git"


# 后续提取视频可能需要的
# 安装 smplx
cd smplx-master
pip install -e .

# 安装 smpl_sim
cd ../SMPLSim-master
pip install -e .
