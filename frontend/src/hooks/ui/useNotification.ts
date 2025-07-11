import { useCallback, useRef } from "react";
import type { Notification } from "@/store/types";
import useUIStore from "@/store/uiStore";

/**
 * Hook for managing notifications with automatic removal functionality
 *
 * This hook provides a clean interface for adding notifications that
 * automatically remove themselves after a specified duration, keeping
 * side effects out of the store.
 *
 * @returns Object with methods to show different types of notifications
 */
export function useNotification() {
	const { addNotification, removeNotification } = useUIStore();
	const timeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

	const showNotification = useCallback(
		(notification: Omit<Notification, "id" | "createdAt">) => {
			const id = addNotification(notification);

			// Handle auto-removal if duration is specified and not 0
			if (notification.duration !== 0) {
				const timeout = setTimeout(() => {
					removeNotification(id);
					timeoutRefs.current.delete(id);
				}, notification.duration || 5000);

				timeoutRefs.current.set(id, timeout);
			}

			return id;
		},
		[addNotification, removeNotification],
	);

	const success = useCallback(
		(title: string, message?: string, duration?: number) => {
			return showNotification({ type: "success", title, message, duration });
		},
		[showNotification],
	);

	const error = useCallback(
		(title: string, message?: string, duration?: number) => {
			return showNotification({ type: "error", title, message, duration });
		},
		[showNotification],
	);

	const warning = useCallback(
		(title: string, message?: string, duration?: number) => {
			return showNotification({ type: "warning", title, message, duration });
		},
		[showNotification],
	);

	const info = useCallback(
		(title: string, message?: string, duration?: number) => {
			return showNotification({ type: "info", title, message, duration });
		},
		[showNotification],
	);

	// Clean up timeouts on unmount
	const clearAllTimeouts = useCallback(() => {
		timeoutRefs.current.forEach((timeout) => clearTimeout(timeout));
		timeoutRefs.current.clear();
	}, []);

	return {
		showNotification,
		success,
		error,
		warning,
		info,
		clearAllTimeouts,
	};
}
