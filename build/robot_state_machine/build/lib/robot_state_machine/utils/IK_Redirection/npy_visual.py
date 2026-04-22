import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from scipy.spatial.transform import Rotation as R
import os

path = "/tmp/robot_action.npy"
# path = "/home/sunrise/TWStateMachine/src/robot_state_machine/robot_state_machine/utils/IK_Redirection/input/motion_4.npy"
data = np.load(path, allow_pickle=True)

# 兼容：0维object包
if isinstance(data, np.ndarray) and data.shape == () and data.dtype == object:
    data = data.item()   # dict

# 从包里取 motion
motion = data["motion"] if isinstance(data, dict) and "motion" in data else data
motion = np.asarray(motion)

# 统一转成 (N,22,3)
if motion.ndim == 4 and motion.shape[1:3] == (22, 3):
    # (1,22,3,T) -> (T,22,3)
    seq = motion[0].transpose(2, 0, 1)
elif motion.ndim == 3 and motion.shape[0:2] == (22, 3):
    # (22,3,T) -> (T,22,3)
    seq = motion.transpose(2, 0, 1)
elif motion.ndim == 3 and motion.shape[1:3] == (22, 3):
    # 已经是 (T,22,3)
    seq = motion
else:
    raise ValueError(f"Unsupported motion shape: {motion.shape}")

N, J, _ = seq.shape
print("seq shape:", seq.shape)  # 应该是 (T,22,3)

rot = R.from_quat([0.5, 0.5, 0.5, 0.5]).as_matrix()
seq = seq @ rot.T

# A common SMPL-like 22-joint connectivity (may differ slightly by dataset)
# indices: 0 pelvis, 1 L_hip, 2 R_hip, 3 spine1, 4 L_knee, 5 R_knee, 6 spine2,
# 7 L_ankle, 8 R_ankle, 9 spine3, 10 L_foot, 11 R_foot, 12 neck,
# 13 L_collar, 14 R_collar, 15 head, 16 L_shoulder, 17 R_shoulder,
# 18 L_elbow, 19 R_elbow, 20 L_wrist, 21 R_wrist
edges = [
    (0,1),(0,2),(0,3),
    (1,4),(4,7),(7,10),
    (2,5),(5,8),(8,11),
    (3,6),(6,9),(9,12),
    (12,15),
    (12,13),(13,16),(16,18),(18,20),
    (12,14),(14,17),(17,19),(19,21),
]

# Axis limits
mins = seq.reshape(-1,3).min(axis=0)
maxs = seq.reshape(-1,3).max(axis=0)
center = (mins + maxs) / 2
span = (maxs - mins).max() * 0.6
xlim = (center[0]-span, center[0]+span)
ylim = (center[1]-span, center[1]+span)
zlim = (center[2]-span, center[2]+span)

fig = plt.figure(figsize=(6.5, 6.5))
ax = fig.add_subplot(111, projection="3d")
ax.set_title("dance.npy (22 joints) - 3D animation")
ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_zlim(*zlim)
ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
ax.view_init(elev=10, azim=0)

# Draw initial
pts = seq[0]
sc = ax.scatter(pts[:,0], pts[:,1], pts[:,2], s=18)
lines = []
for a,b in edges:
    ln, = ax.plot([pts[a,0], pts[b,0]],
                  [pts[a,1], pts[b,1]],
                  [pts[a,2], pts[b,2]], linewidth=2)
    lines.append(ln)

def update(frame):
    pts = seq[frame]
    sc._offsets3d = (pts[:,0], pts[:,1], pts[:,2])
    for ln, (a,b) in zip(lines, edges):
        ln.set_data([pts[a,0], pts[b,0]], [pts[a,1], pts[b,1]])
        ln.set_3d_properties([pts[a,2], pts[b,2]])
    ax.set_title(f"dance.npy - frame {frame+1}/{N}")
    return [sc] + lines

anim = FuncAnimation(fig, update, frames=N, interval=50, blit=False)

out_gif = "./output/kick_vis.gif"
anim.save(out_gif, writer=PillowWriter(fps=20))

# Save a first-frame static image too
out_png = "./output/kick_frame0.png"
plt.figure(figsize=(6.5, 6.5))
ax2 = plt.axes(projection="3d")
ax2.set_title("motion_4.npy - frame 0")
ax2.set_xlim(*xlim); ax2.set_ylim(*ylim); ax2.set_zlim(*zlim)
ax2.set_xlabel("X"); ax2.set_ylabel("Y"); ax2.set_zlabel("Z")
ax2.view_init(elev=15, azim=-60)
pts0 = seq[0]
ax2.scatter(pts0[:,0], pts0[:,1], pts0[:,2], s=18)
for a,b in edges:
    ax2.plot([pts0[a,0], pts0[b,0]],
             [pts0[a,1], pts0[b,1]],
             [pts0[a,2], pts0[b,2]], linewidth=2)
plt.tight_layout()
plt.savefig(out_png, dpi=160)
plt.close("all")

(out_gif, out_png, seq.shape, float(span))
