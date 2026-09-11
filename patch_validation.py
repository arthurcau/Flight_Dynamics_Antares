import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

validation_code = """
        # --- STATISTICAL VALIDATION OF REAL LANDING SITES ---
        # Calculate Mahalanobis distance to see if simulation "explains" the landing
        try:
            from scipy.stats import chi2
            points_xy = np.vstack((x, y))
            cov_matrix = np.cov(points_xy)
            inv_cov = np.linalg.inv(cov_matrix)
            mean_x, mean_y = np.mean(x), np.mean(y)
            
            def calculate_probability(px, py):
                delta = np.array([px - mean_x, py - mean_y])
                mahalanobis_sq = np.dot(np.dot(delta.T, inv_cov), delta)
                # Chi-square CDF with 2 DoF gives the probability containment ellipse size
                return chi2.cdf(mahalanobis_sq, 2) * 100
                
            p_nose = calculate_probability(x_nose, y_nose)
            p_fuse = calculate_probability(x_fuse, y_fuse)
            
            # Add text box with validation results
            val_text = (
                f"STATISTICAL VALIDATION\\n"
                f"Nose Cone lies on the {p_nose:.1f}% ellipse\\n"
                f"Fuselage lies on the {p_fuse:.1f}% ellipse\\n"
                f"\\nConclusion: "
            )
            
            if p_nose <= 99.7 and p_fuse <= 99.7:
                val_text += "COHERENT (Explained by Sim)"
                box_color = 'lightgreen'
            else:
                val_text += "OUTLIER (Missing Physics/Wind)"
                box_color = 'salmon'
                
            plt.gca().text(0.02, 0.98, val_text, transform=plt.gca().transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor=box_color, alpha=0.8))
        except Exception as e:
            print(f"[Monte Carlo] Validation calc failed: {e}")
            pass
        # ----------------------------------------------------
"""

marker = "        plt.scatter(x_fuse, y_fuse, marker='P', color='darkorange', s=150, zorder=10, edgecolors='black', label='Fuselage Landing Site')"

if marker in content:
    content = content.replace(marker, marker + "\n" + validation_code)
    with open("source/antares_fd/simulation/plotters.py", "w") as f:
        f.write(content)
    print("Patched 2D plot with validation.")
else:
    print("Could not find marker.")
