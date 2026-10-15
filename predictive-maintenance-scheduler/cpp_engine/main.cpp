#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <iomanip>
using namespace std;

struct MaintenanceTask {
    int taskId;
    string machineId;
    double failureRisk;
    int urgency;
    int repairHours;
    double priority;
};

double calculatePriority(double risk, int urgency) {
    return (0.7 * risk) + (0.3 * urgency);
}

bool compareTasks(MaintenanceTask a, MaintenanceTask b) {
    return a.priority > b.priority;
}

int main() {
    vector<MaintenanceTask> tasks = {
        {1, "M-101", 92, 90, 4, 0},
        {2, "M-102", 45, 50, 2, 0},
        {3, "M-103", 78, 75, 3, 0},
        {4, "M-104", 25, 30, 2, 0},
        {5, "M-105", 85, 65, 5, 0}
    };

    for (auto &task : tasks) {
        task.priority =
            calculatePriority(task.failureRisk, task.urgency);
    }

    sort(tasks.begin(), tasks.end(), compareTasks);

    cout << "\nPREDICTIVE MAINTENANCE SCHEDULER\n";
    cout << "===============================================\n";
    cout << left << setw(10) << "Machine"
         << setw(12) << "Risk (%)"
         << setw(12) << "Urgency"
         << setw(12) << "Priority"
         << "Repair (h)\n";

    cout << "-----------------------------------------------\n";

    for (const auto &task : tasks) {
        cout << left << setw(10) << task.machineId
             << setw(12) << task.failureRisk
             << setw(12) << task.urgency
             << setw(12) << fixed << setprecision(1)
             << task.priority
             << task.repairHours << '\n';
    }

    cout << "\nScheduling completed successfully.\n";
    cout << "Highest-priority machine: "
         << tasks.front().machineId << '\n';

    return 0;
}