import torch 
import numpy as np
import phc.utils.rotation_conversions as tRot
import xml.etree.ElementTree as ETree
from easydict import EasyDict
import scipy.ndimage.filters as filters
import smpl_sim.poselib.core.rotation3d as pRot




class Humanoid_Batch:
    def __init__(self, mjcf_file = f"src/robot_state_machine/robot_state_machine/utils/IK_Redirection/data/Assembly/Assembly.SLDASM.urdf", extend_hand =  False, extend_head = False, device = torch.device("cpu")):
        self.mjcf_data = mjcf_data = self.from_urdf(mjcf_file)
        self.extend_hand = extend_hand
        self.extend_head = extend_head
        if extend_hand:
            self.model_names = mjcf_data['node_names'] + ["left_hand_link", "right_hand_link"]
            self._parents = torch.cat((mjcf_data['parent_indices'], torch.tensor([15, 19]))).to(device) # Adding the hands joints
            arm_length = 0.3
            self._offsets = torch.cat((mjcf_data['local_translation'], torch.tensor([[arm_length, 0, 0], [arm_length, 0, 0]])), dim = 0)[None, ].to(device)
            self._local_rotation = torch.cat((mjcf_data['local_rotation'], torch.tensor([[1, 0, 0, 0], [1, 0, 0, 0]])), dim = 0)[None, ].to(device)
            self._remove_idx = 2
        else:
            self._parents = mjcf_data['parent_indices']
            self.model_names = mjcf_data['node_names']
            self._offsets = mjcf_data['local_translation'][None, ].to(device)
            self._local_rotation = mjcf_data['local_rotation'][None, ].to(device)
            
        if extend_head:
            self._remove_idx = 3
            self.model_names = self.model_names + ["head_link"]
            self._parents = torch.cat((self._parents, torch.tensor([0]).to(device))).to(device) # Adding the hands joints
            head_length = 0.75
            self._offsets = torch.cat((self._offsets, torch.tensor([[[0, 0, head_length]]]).to(device)), dim = 1).to(device)
            self._local_rotation = torch.cat((self._local_rotation, torch.tensor([[[1, 0, 0, 0]]]).to(device)), dim = 1).to(device)
            
        self.H1_ROTATION_AXIS=mjcf_data['joints_axis']
        self.joints_range = mjcf_data['joints_range'].to(device)
        self._local_rotation_mat = tRot.quaternion_to_matrix(self._local_rotation).float() # w, x, y ,z
    #从MJCF文件加载骨架数据
    def from_urdf(self,path):
        tree = ETree.parse(path)
        xml_doc_root = tree.getroot()

        # 查找所有链接和关节
        links = xml_doc_root.findall("link")
        joints = xml_doc_root.findall("joint")

        node_names = []
        parent_indices = []
        local_translation = []
        local_rotation = []
        joints_range = []
        joints_axis = []  
        # 创建一个字典来存储链接名称到索引的映射
        link_name_to_index = {}
        for i, link in enumerate(links):
            link_name = link.attrib.get("name")
            link_name_to_index[link_name] = i
            node_names.append(link_name)
            # 第一个链接是根链接
            if i == 0:
                parent_indices.append(-1)
                local_translation.append(np.array([0.0, 0.0, 0.0]))
                local_rotation.append(np.array([1.0, 0.0, 0.0, 0.0]))
            else:
                parent_indices.append(-1)  
                local_translation.append(np.array([0.0, 0.0, 0.0]))
                local_rotation.append(np.array([1.0, 0.0, 0.0, 0.0]))

        # 遍历所有关节来构建链接之间的关系
        for joint in joints:
            joint_name = joint.attrib.get("name")
            parent_link_name = joint.find("parent").attrib.get("link")
            child_link_name = joint.find("child").attrib.get("link")
            origin = joint.find("origin")
            if origin is not None:
                pos = origin.attrib.get("xyz", "0 0 0").split()
                pos = np.fromstring(" ".join(pos), dtype=float, sep=" ")
                quat = origin.attrib.get("rpy", "0 0 0").split()
                # 将RPY转换为四元数（这里简化处理，实际应用中需要更准确的转换）
                quat = np.fromstring(" ".join(quat), dtype=float, sep=" ")
                # 假设四元数为 [w, x, y, z]，这里可能需要更准确的转换
                quat = np.insert(quat, 0, 1.0)  # 简化处理，实际应使用正确的RPY到四元数转换
            else:
                pos = np.array([0.0, 0.0, 0.0])
                quat = np.array([1.0, 0.0, 0.0, 0.0])
            # 提取关节轴向
            axis = joint.find("axis")
            axis_xyz = np.array([0.0, 0.0, 1.0])  # 默认轴向
            if axis is not None:
                xyz = axis.attrib.get("xyz", "0 0 1").split()
                axis_xyz = np.fromstring(" ".join(xyz), dtype=float, sep=" ")
            joints_axis.append(axis_xyz)
            # 更新子链接的父链接索引、局部平移和旋转
            if child_link_name in link_name_to_index:
                child_index = link_name_to_index[child_link_name]
                parent_index = link_name_to_index.get(parent_link_name, -1)
                parent_indices[child_index] = parent_index
                local_translation[child_index] = pos
                local_rotation[child_index] = quat

            # 提取关节范围
            limit = joint.find("limit")
            if limit is not None:
                lower = limit.attrib.get("lower", "-inf")
                upper = limit.attrib.get("upper", "inf")
                if lower != "-inf" and upper != "inf":
                    joints_range.append(np.array([float(lower), float(upper)]))
            
        # 转换为PyTorch张量
        parent_indices = torch.from_numpy(np.array(parent_indices, dtype=np.int32))
        local_translation = torch.from_numpy(np.array(local_translation, dtype=np.float32))
        local_rotation = torch.from_numpy(np.array(local_rotation, dtype=np.float32))
        joints_range = torch.from_numpy(np.array(joints_range, dtype=np.float32))
        joints_axis = torch.from_numpy(np.array(joints_axis, dtype=np.float32)) 
        return {
            "node_names": node_names,
            "parent_indices": parent_indices,
            "local_translation": local_translation,
            "local_rotation": local_rotation,
            "joints_range": joints_range,
            "joints_axis": joints_axis  
        }
    #根据给定的关节角度（pose）和根节点平移（trans），计算每个关节的全局位置和旋转。
    def fk_batch(self, pose, trans, convert_to_mat=True, return_full = False, dt=1/30):
        device, dtype = pose.device, pose.dtype
        pose_input = pose.clone()
        B, seq_len = pose.shape[:2]
        pose = pose[..., :len(self._parents), :] # H1 fitted joints might have extra joints
        if self.extend_hand and self.extend_head and pose.shape[-2] == 22:
            pose = torch.cat([pose, torch.zeros(B, seq_len, 1, 3).to(device).type(dtype)], dim = -2) # adding hand and head joints
        if convert_to_mat:
            pose_quat = tRot.axis_angle_to_quaternion(pose)
            pose_mat = tRot.quaternion_to_matrix(pose_quat)
        else:
            pose_mat = pose
        if pose_mat.shape != 5:
            pose_mat = pose_mat.reshape(B, seq_len, -1, 3, 3)
        J = pose_mat.shape[2] - 1  # Exclude root
        
        wbody_pos, wbody_mat = self.forward_kinematics_batch(pose_mat[:, :, 1:], pose_mat[:, :, 0:1], trans)
        
        return_dict = EasyDict()
        
        
        wbody_rot = tRot.wxyz_to_xyzw(tRot.matrix_to_quaternion(wbody_mat))
        if self.extend_hand:
            if return_full:
                return_dict.global_velocity_extend = self._compute_velocity(wbody_pos, dt) 
                return_dict.global_angular_velocity_extend = self._compute_angular_velocity(wbody_rot, dt)
                
            return_dict.global_translation_extend = wbody_pos.clone()
            return_dict.global_rotation_mat_extend = wbody_mat.clone()
            return_dict.global_rotation_extend = wbody_rot
            
            wbody_pos = wbody_pos[..., :-self._remove_idx, :]
            wbody_mat = wbody_mat[..., :-self._remove_idx, :, :]
            wbody_rot = wbody_rot[..., :-self._remove_idx, :]
        
        return_dict.global_translation = wbody_pos
        return_dict.global_rotation_mat = wbody_mat
        return_dict.global_rotation = wbody_rot
            
        if return_full:
            rigidbody_linear_velocity = self._compute_velocity(wbody_pos, dt)  # Isaac gym is [x, y, z, w]. All the previous functions are [w, x, y, z]
            rigidbody_angular_velocity = self._compute_angular_velocity(wbody_rot, dt)
            return_dict.local_rotation = tRot.wxyz_to_xyzw(pose_quat)
            return_dict.global_root_velocity = rigidbody_linear_velocity[..., 0, :]
            return_dict.global_root_angular_velocity = rigidbody_angular_velocity[..., 0, :]
            return_dict.global_angular_velocity = rigidbody_angular_velocity
            return_dict.global_velocity = rigidbody_linear_velocity
            
            if self.extend_hand or self.extend_head:
                return_dict.dof_pos = pose.sum(dim = -1)[..., 1:][..., :-self._remove_idx] # you can sum it up since unitree's each joint has 1 dof. Last two are for hands. doesn't really matter. 
            else:
                return_dict.dof_pos = pose.sum(dim = -1)[..., 1:] # you can sum it up since unitree's each joint has 1 dof. Last two are for hands. doesn't really matter. 
            
            dof_vel = ((return_dict.dof_pos[:, 1:] - return_dict.dof_pos[:, :-1] )/dt)
            return_dict.dof_vels = torch.cat([dof_vel, dof_vel[:, -2:-1]], dim = 1)
            return_dict.fps = int(1/dt)
        
        return return_dict
    
    #计算每个关节的全局位置和旋转
    def forward_kinematics_batch(self, rotations, root_rotations, root_positions):
        """
        Perform forward kinematics using the given trajectory and local rotations.
        Arguments (where B = batch size, J = number of joints):
         -- rotations: (B, J, 4) tensor of unit quaternions describing the local rotations of each joint.
         -- root_positions: (B, 3) tensor describing the root joint positions.
        Output: joint positions (B, J, 3)
        """
        
        device, dtype = root_rotations.device, root_rotations.dtype
        B, seq_len = rotations.size()[0:2]
        J = self._offsets.shape[1]
        positions_world = []
        rotations_world = []

        expanded_offsets = (self._offsets[:, None].expand(B, seq_len, J, 3).to(device).type(dtype))
        # print(expanded_offsets.shape, J)

        for i in range(J):
            if self._parents[i] == -1:
                positions_world.append(root_positions)
                rotations_world.append(root_rotations)
            else:
                jpos = (torch.matmul(rotations_world[self._parents[i]][:, :, 0], expanded_offsets[:, :, i, :, None]).squeeze(-1) + positions_world[self._parents[i]])
                rot_mat = torch.matmul(rotations_world[self._parents[i]], torch.matmul(self._local_rotation_mat[:,  (i):(i + 1)], rotations[:, :, (i - 1):i, :]))
                # rot_mat = torch.matmul(rotations_world[self._parents[i]], rotations[:, :, (i - 1):i, :])
                # print(rotations[:, :, (i - 1):i, :].shape, self._local_rotation_mat.shape)
                
                positions_world.append(jpos)
                rotations_world.append(rot_mat)
        
        positions_world = torch.stack(positions_world, dim=2)
        rotations_world = torch.cat(rotations_world, dim=2)
        return positions_world, rotations_world
    def get_axis(self):
        return self.H1_ROTATION_AXIS
    @staticmethod
    def _compute_velocity(p, time_delta, guassian_filter=True):
        velocity = np.gradient(p.numpy(), axis=-3) / time_delta
        if guassian_filter:
            velocity = torch.from_numpy(filters.gaussian_filter1d(velocity, 2, axis=-3, mode="nearest")).to(p)
        else:
            velocity = torch.from_numpy(velocity).to(p)
        
        return velocity
    
    @staticmethod
    def _compute_angular_velocity(r, time_delta: float, guassian_filter=True):
        # assume the second last dimension is the time axis
        diff_quat_data = pRot.quat_identity_like(r).to(r)
        diff_quat_data[..., :-1, :, :] = pRot.quat_mul_norm(r[..., 1:, :, :], pRot.quat_inverse(r[..., :-1, :, :]))
        diff_angle, diff_axis = pRot.quat_angle_axis(diff_quat_data)
        angular_velocity = diff_axis * diff_angle.unsqueeze(-1) / time_delta
        if guassian_filter:
            angular_velocity = torch.from_numpy(filters.gaussian_filter1d(angular_velocity.numpy(), 2, axis=-3, mode="nearest"),)
        return angular_velocity  



if __name__ == "__main__":
    testhum=Humanoid_Batch(mjcf_file = f"/home/usr2/H20/human2humanoid/data/Assembly/Assembly.SLDASM.urdf")

    h1_rotation_axis=testhum.get_axis()
    print(h1_rotation_axis.shape)
    N=2
    dof_pos = torch.zeros(1, N, 28, 1)
    gt_root_rot= torch.zeros( N, 3)
    pose_aa_h1_new = torch.cat([gt_root_rot[None, :, None], h1_rotation_axis * dof_pos, torch.zeros((1, N, 2, 3))], axis = 2)
    #正向运动学计算的结果
    root_trans_offset= torch.zeros((N, 3))  # 假设根节点平移为零
    # print("pose_aa_h1_new shape:", pose_aa_h1_new.shape)
    # print("root_trans_offset[None, ] shape:", root_trans_offset[None, ].shape)
    # fk_return = testhum.fk_batch(pose_aa_h1_new, root_trans_offset[None, ])

