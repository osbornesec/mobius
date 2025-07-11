/**
 * Example usage of the useNotification hook
 * This file demonstrates how to use notifications with auto-removal
 */

import { useNotification } from "./useNotification";

export function NotificationExample() {
	const { success, error, showNotification } = useNotification();

	const handleSuccess = () => {
		// Simple success notification with default 5s duration
		success("Operation completed", "Your changes have been saved");
	};

	const handleError = () => {
		// Error notification with custom 10s duration
		error("Operation failed", "Please try again later", 10000);
	};

	const handlePersistent = () => {
		// Persistent notification (duration: 0 means it won't auto-remove)
		showNotification({
			type: "info",
			title: "Important update",
			message: "This notification will stay until manually dismissed",
			duration: 0,
		});
	};

	return (
		<div>
			<button type="button" onClick={handleSuccess}>
				Show Success
			</button>
			<button type="button" onClick={handleError}>
				Show Error
			</button>
			<button type="button" onClick={handlePersistent}>
				Show Persistent
			</button>
		</div>
	);
}
